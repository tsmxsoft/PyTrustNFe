# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import os
import sys
import requests
import traceback
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.dsf_abrasf203.assinatura import Assinatura
from lxml import etree





def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    if method == "RecepcionarLoteRps" \
        or method == "RecepcionarLoteRpsSincrono":
        referencia = kwargs.get("nfse").get("numero_lote")
            
        xml_signed_send = signer.assina_xml(
            xml_send, "lote:{0}".format(referencia))
        
        
    elif method == "CancelarNfse":
        xml_signed_send = signer.assina_xml(xml_send, reference="rps:%s" %str(kwargs["nfse"]["rps"]["numero"]))
    
    elif method in ["ConsultarLoteRps", "ConsultarNfsePorRps"]:
        xml_signed_send = signer.assina_xml_consulta(xml_send)
    
    else:
        xml_signed_send = etree.tostring(xml_send)

    print('----- XML -----')
    print(xml_signed_send)

    return xml_signed_send

def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")

    base_url = kwargs.get("base_url", None)

    if not base_url:
        raise ValueError("URL é obrigatória para envio do XML")
    

    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, False, soap_body=xml_send, method=method)

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)


    headers = {
        "SOAPAction": "",
        "Content-length": str(len(soap)),
        "Content-Type": "text/xml; charset=utf-8",
    }

    request = requests.post(base_url, data=soap, cert=(cert, key), headers=headers, verify=False)
    response, obj = sanitize_response(request.content)
    return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }



def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRps", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
        print(kwargs["xml"])
    return _send(certificado, "RecepcionarLoteRps", **kwargs)



def xml_cancelar_nfse(certificado, **kwargs):
    response = _render(certificado, "CancelarNfse", **kwargs)
    print(response)
    return response

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    response = _send(certificado, "CancelarNfse", **kwargs)
    xml = None

    try:
        #Conversão a objeto e Busca pelo elemento Nfse
        xml_obj = response['object']['CancelarNfseResponse']

        #Caso haja algum erro, as mensagens serão retornadas
        if xml_obj.find(".//ListaMensagemRetorno") is not None:
            xml_obj = xml_obj.find(".//ListaMensagemRetorno")

        #Conversão de volta a string
        xml = etree.tostring(xml_obj)
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

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarLoteRps", **kwargs)

    xml = None

    try:
        res, xml_obj = sanitize_response(response['received_xml'])

        if xml_obj.find(".//CompNfse") is not None:
            xml_obj = xml_obj.find(".//CompNfse")

        if xml_obj.find(".//ListaMensagemRetorno") is not None:
            xml_obj = xml_obj.find(".//ListaMensagemRetorno")

        xml = etree.tostring(xml_obj, xml_declaration=False, pretty_print=True)
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


def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfsePorRps", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
    xml = None

    try:
        res, xml_obj = sanitize_response(response['received_xml'])

        if xml_obj.find(".//CompNfse") is not None:
            xml_obj = xml_obj.find(".//CompNfse")

        if xml_obj.find(".//ListaMensagemRetorno") is not None:
            xml_obj = xml_obj.find(".//ListaMensagemRetorno")
        
        #Conversão de volta a string
        xml = etree.tostring(xml_obj, xml_declaration=False, pretty_print=True)
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


