# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import re
import os
import sys
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.imp2.assinatura import Assinatura
from lxml import etree
from requests import Session
import requests


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    referencia = ""
    if method in ["RecepcionarLoteRps", "RecepcionarLoteRpsSincrono"]:
        referencia = kwargs.get("nfse").get("numero_lote")

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    xml_send = etree.fromstring(
        xml_string_send, parser=parser)
    

    if method == "RecepcionarLoteRps" \
        or method == "RecepcionarLoteRpsSincrono":
        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps:{0}{1}".format(
                item.get('numero'), item.get('serie'))

            xml_signed_send = signer.assina_xml(xml_send, reference)

    else:
        xml_signed_send = etree.tostring(xml_send)

    return xml_signed_send


def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")

    url = kwargs["base_url"]

    # Dados obrigatórios para autenticação de qualquer método
    usuario = kwargs.get("nfse").get("usuario")
    senha = kwargs.get("nfse").get("senha", None)

    if not usuario or not senha:
        raise ValueError("Usuário e senha são obrigatórios para autenticação")
    if not url:
        raise ValueError("URL base é obrigatória para envio do XML")


    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, **{"soap_body":xml_send, "method": method })

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    action = "%s" %(method)
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": action,
        "Content-length": str(len(soap))
    }

    request = requests.post(url, data=soap, headers=headers, auth=(usuario, senha))
    response, obj = sanitize_response(request.content.decode('utf8', 'ignore'))

    try:
        return {"sent_xml": str(soap), "received_xml": str(response.encode('utf8')), "object": obj.Body }
    except:
        return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }
    

# RECEPCIONAR LOTE RPS
def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "EnviarLoteRpsEnvio", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "EnviarLoteRpsEnvio", **kwargs)

# CANCELAR NFSE
def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    response = _send(certificado, "CancelarNfse", **kwargs)
    xml = None

    try:
        xml_obj = response['object']['CancelarNfseResposta']

        if xml_obj.find(".//InfPedidoCancelamento"):
            xml_obj = xml_obj.find(".//InfPedidoCancelamento")
        
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


# CONSULTAR LOTE RPS
def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarLoteRps", **kwargs)
    xml = None

    try:
        xml_obj = response['object']['ConsultarLoteRpsResposta']
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


# CONSULTAR NFSE POR RPS
def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfsePorRps", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
    xml = None

    try:
        xml_obj = response['object']['ConsultarNfseRpsResposta']
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


