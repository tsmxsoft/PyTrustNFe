# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import os
import sys
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_key_and_ca_from_pfx
from pytrustnfe.nfse.betha.assinatura import Assinatura
from lxml import etree
from zeep.transports import Transport
from requests import Session
import requests
from datetime import datetime, timedelta
from pytrustnfe import get_version

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    referencia = ""
    if method in ["RecepcionarLoteRps","RecepcionarLoteRpsSincrono"]:
        referencia = kwargs.get("nfse").get("numero_lote")

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    if method == "RecepcionarLoteRps" \
        or method == "RecepcionarLoteRpsSincrono":
        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps:{0}{1}".format(
                item.get('numero'), item.get('serie'))

            xml_signed_send = signer.assina_xml(xml_send, reference)
    elif method == "CancelarNfse":
        xml_signed_send = signer.assina_xml(xml_send,"rps:%s" %str(kwargs["nfse"]["rps"]["numero"]))
    else:
        xml_signed_send = etree.tostring(xml_send)

    return xml_signed_send

def _send(certificado, method, **kwargs):

    path = os.path.join(os.path.dirname(__file__), "templates")
    url = kwargs["base_url"]
    url = url.lower().replace("?wsdl","")
    url = url + 'soap/'

    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, **{"soap_body":xml_send, "method": method })

    action = "http://nfse.abrasf.org.br/%s" %(method)
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": action,
        "User-Agent": "PyTrustNFe3/%s" %(str(get_version())),
        "Content-length": str(len(soap))
    }
    with extract_cert_key_and_ca_from_pfx(certificado.pfx, certificado.password) as cert:
        request = requests.post(url, data=soap, headers=headers, cert=cert)
        response, obj = sanitize_response(request.content)
        try:
            return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }
        except:
            return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRps", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRps", **kwargs)

def xml_gerar_nfse(certificado, **kwargs):
    return _render(certificado, "GerarNfse", **kwargs)

def gerar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_gerar_nfse(certificado, **kwargs)
    return _send(certificado, "GerarNfse", **kwargs)

def xml_envio_lote_rps_sincrono(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRpsSincrono", **kwargs)

def envio_lote_rps_sincrono(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_envio_lote_rps_sincrono(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRpsSincrono", **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    response = _send(certificado, "CancelarNfse", **kwargs)
    xml = None

    try:
        #Conversão a objeto e Busca pelo elemento Nfse
        xml_obj = response['object']
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
    except Exception as err:
        pass

    return xml

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarLoteRps", **kwargs)
    xml = None
    try:
        xml_clean = re.sub(r'\<\?xml.+\?\>\n?','',response['object']['ConsultarLoteRpsResposta']['return'].text)
        res, xml_obj = sanitize_response(xml_clean)
        xml = etree.tostring(xml_obj,xml_declaration=False)
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

def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfsePorRps", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
    xml = None
    print(response['received_xml'])

    try:
        res, xml_obj = sanitize_response(response['object']['ConsultarNfsePorRpsResponse']['return'].text)
        xml_obj = xml_obj.find(".//CompNfse")
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
        pass

    return xml
