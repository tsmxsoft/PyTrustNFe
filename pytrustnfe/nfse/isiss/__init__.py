# -*- coding: utf-8 -*-
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from OpenSSL import crypto
from base64 import b64encode

from requests import Session
from zeep import Client
from zeep.transports import Transport
from requests.packages.urllib3 import disable_warnings

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura
from lxml import etree
import sys

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    referencia = ""
    if method == "RecepcionarLoteRpsSincrono" or method == "RecepcionarLoteRps":
        referencia = kwargs.get("nfse").get("numero_lote")

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    for item in kwargs["nfse"]["lista_rps"]:
        reference = "rps:{0}{1}".format(
            item.get('numero'), item.get('serie'))

        signer.assina_xml(xml_send, reference, remove_attrib='Id')

    xml_signed_send = signer.assina_xml(
        xml_send, "lote:{0}".format(referencia))

    print ('--- xml ---')
    print (xml_signed_send)

    return xml_signed_send

def _render_unsigned(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(remove_blank_text=True, 
                             remove_comments=True, 
                             strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    xml = render_xml(path, "%s.xml" % method, True, **kwargs)

    reference = "rps:{0}{1}".format(kwargs["nfse"]['rps']['numero'], 
                                    kwargs["nfse"]['rps']['serie'])
    xml_send = etree.fromstring(xml, parser=parser)
    xml = signer.assina_xml(xml_send, reference, remove_attrib='Id')

    return xml

def _send(certificado, method, **kwargs):
    base_url = ""
    if kwargs["ambiente"] == "homologacao":
        base_url = "https://wsnfse.vitoria.es.gov.br/homologacao/NotaFiscalService.asmx?WSDL"
    else:
        base_url = kwargs.get("base_url") or "https://wsnfse.vitoria.es.gov.br/producao/NotaFiscalService.asmx?WSDL"

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    session = Session()
    session.cert = (cert, key)
    session.trust_env = False
    transport = Transport(session=session)

    client = Client(wsdl=base_url, transport=transport)
    xml = client.service[method](kwargs["xml"])
    xml, obj = sanitize_response(xml)

    print ('--- xml response ---')
    print (xml)

    return {"sent_xml": kwargs["xml"], "received_xml": xml, "object": obj}
    

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRps", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRps", **kwargs)

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, "ConsultarLoteRps", **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "cancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "cancelarNfse", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)

    print (kwargs["xml"])
    
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
    xml = None

    try:
        xml_element = response['object'].find('.//Nfse')

        if sys.version_info[0] > 2:
            xml = str(etree.tostring(xml_element, encoding=str))
        else:
            xml = str(etree.tostring(xml_element, encoding="utf8"))
            
        xml = xml.replace('&#13;', '')
    except:
        pass

    return xml


def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render_unsigned(certificado, "ConsultarNfsePorRps", **kwargs)