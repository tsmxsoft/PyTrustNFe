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

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)
    if method == "RecepcionarLoteRpsSincrono" or method == "RecepcionarLoteRps":
        referencia = kwargs.get("nfse").get("numero_lote")

        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps:{0}{1}".format(
                item.get('numero'), item.get('serie'))

            signer.assina_xml(xml_send, reference, remove_attrib='Id')

        xml_signed_send = signer.assina_xml(
            xml_send, "lote:{0}".format(referencia))
    else:
        xml_signed_send = xml_string_send

    print ('--- xml ---')
    print (xml_signed_send)

    return xml_signed_send

def _render_unsigned(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(remove_blank_text=True, 
                             remove_comments=True, 
                             strip_cdata=False
    )

    xml = render_xml(path, "%s.xml" % method, True, **kwargs)

    xml_send = etree.fromstring(xml, parser=parser)

    return xml_send

def _send(certificado, method, **kwargs):
    base_url = kwargs["base_url"]

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    client = Client(wsdl='{}'.format(base_url), transport=transport)
    with client.settings(strict=False, raw_response=True):
        xml_send = {
            "nfseDadosMsg": kwargs["xml"],
            "nfseCabecMsg": """<?xml version="1.0"?>
            <cabecalho versao="1.00" xmlns="http://www.abrasf.org.br/nfse.xsd">
            <versaoDados>2.04</versaoDados>
            </cabecalho>""",
        }

        if method in ["ConsultarLoteRps", "ConsultarNfsePorRps"]:
            xml_send = {
                "nfseDadosMsg": kwargs["xml"],
                "nfseCabecMsg": """<?xml version='1.0'?>
                <ns1:cabecalho xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'
                xmlns:ns2='http://www.w3.org/2000/09/xmldsig#'
                xmlns:ns1='http://www.abrasf.org.br/nfse.xsd'
                xsi:schemaLocation='http://www.w3.org/2000/09/xmldsig#
                abrasfteste/xmldsig-core-schema20020212.xsd
                http://www.abrasf.org.br/nfse.xsd
                abrasfteste/nfse_v2-04.xsd'>
                    <ns1:versaoDados>2.04</ns1:versaoDados>
                </ns1:cabecalho>""",
            }


        response = client.service[method](xml_send)
        print(response.content)
        response, obj = sanitize_response(response.text)

        print('--- xml response ---')
        print(response)

        return {"sent_xml": xml_send, "received_xml": response, "object": obj}
    

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
    response = _send(certificado, "ConsultarLoteRps", **kwargs)
    
    xml = None

    try:
        xml_obj = response['object'].find(".//ConsultarLoteRpsResponse")
        if xml_obj.find(".//ListaMensagemRetorno"):
            xml_obj = xml_obj.find(".//ListaMensagemRetorno")

        xml = etree.tostring(xml_obj, xml_declaration=False)
        if sys.version_info[0] > 2:
            from html.parser import HTMLParser
            xml = xml.encode(str)
        else:
            from HTMLParser import HTMLParser
            xml = xml.encode('utf-8','ignore')
        #unescape
        xml = HTMLParser().unescape(xml)
    except:
        pass

    return xml

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "CancelarNfse", **kwargs)

def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfsePorRps", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)

    
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
    xml = None
    import traceback
    try:
        xml_obj = response['object'].find(".//ConsultarNfsePorRpsResponse")
        xml = etree.tostring(xml_obj, xml_declaration=False)
        if sys.version_info[0] > 2:
            from html.parser import HTMLParser
            xml = xml.encode(str)
        else:
            from HTMLParser import HTMLParser
            xml = xml.encode('utf-8','ignore')
        #unescape
        xml = HTMLParser().unescape(xml)
        
    except:
        traceback.print_exc()

    return xml

