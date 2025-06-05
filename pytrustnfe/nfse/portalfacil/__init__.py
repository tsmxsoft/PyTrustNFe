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
import logging.config

def _render(certificado, method, **kwargs):
    #Remove final slash
    if kwargs.get('base_url') and kwargs.get('base_url')[-1:] == '/':
        kwargs["base_url"] = kwargs["base_url"][:-1]

    kwargs["base_url"] = kwargs["base_url"].replace("https","http")
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

    if method in ["RecepcionarLoteRps","RecepcionarLoteRpsSincrono"]:
        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps:{0}{1}".format(
                item.get('numero'), item.get('serie'))

            xml_signed_send = signer.assina_xml(xml_send, reference)

        xml_signed_send = signer.assina_xml(
            xml_send, "lote:{0}".format(referencia))
    elif method == "CancelarNfse":
        xml_signed_send = signer.assina_xml(xml_send, "1")

    print ('--- xml ---')
    print (xml_signed_send)

    return xml_signed_send

def _render_unsigned(certificado, method, **kwargs):
    if kwargs.get('base_url') and kwargs.get('base_url')[-1:] == '/':
        kwargs["base_url"] = kwargs["base_url"][:-1]

    kwargs["base_url"] = kwargs["base_url"].replace("https","http")
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(remove_blank_text=True, 
                             remove_comments=True, 
                             strip_cdata=False
    )

    xml = render_xml(path, "%s.xml" % method, True, **kwargs)

    xml_send = etree.fromstring(xml, parser=parser)
    xml = etree.tostring(xml_send)

    return xml

def _send(certificado, method, **kwargs):
    #Remove final slash
    if kwargs.get('base_url') and kwargs.get('base_url')[-1:] == '/':
        kwargs["base_url"] = kwargs["base_url"][:-1]

    base_url = kwargs.get("base_url")

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    client = Client(wsdl='{}/nfseserv/webservice/nfse.wsdl'.format(base_url), transport=transport)
    xml_send = {
        "nfseDadosMsg": kwargs["xml"],
        "nfseCabecMsg": """
        <cabecalho versao="2.04" xmlns="{base_url}/nfseserv/schema/nfse_v204.xsd">
        <versaoDados>2.04</versaoDados>
        </cabecalho>""".replace("{base_url}", base_url.replace("https","http")),
    }

    xml = client.service[method](**xml_send)
    obj = None
    print(xml)
    
    if xml:
        xml, obj = sanitize_response(xml)

    print ('--- xml response ---')
    print (xml)

    return {"sent_xml": xml_send, "received_xml": xml, "object": obj}
    

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRps", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRps", **kwargs)

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render_unsigned(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, "ConsultarLoteRps", **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "CancelarNfse", **kwargs)

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