# -*- coding: utf-8 -*-
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os

from requests import Session
from zeep import Client
from zeep.transports import Transport
from requests.packages.urllib3 import disable_warnings

from pytrustnfe.xml import render_xml
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura
from lxml import etree
import html
import re

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    referencia = ""
    if method == "RecepcionarLoteRps":
        referencia = kwargs.get("nfse").get("numero_lote")

    xml_string_send = render_xml(path, "%s.xml" % "EnvelopeSoap", False, **kwargs)

    #xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    for item in kwargs["nfse"]["lista_rps"]:
        reference = "rps:{0}{1}".format(
            item.get('numero'), item.get('serie'))

        signer.assina_xml(xml_send, reference)

    xml_signed_send = signer.assina_xml(
        xml_send, "lote:{0}".format(referencia))
    
    return xml_signed_send


def _send(certificado, method, **kwargs):
    base_url = ""
    
    if kwargs["ambiente"] == "homologacao":
        base_url = "http://speedgov.com.br/wsmod/Nfes?wsdl"
    else:
        base_url = kwargs["base_url"]

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    client = Client(wsdl=base_url, transport=transport)

    response = transport.post_xml(base_url, etree.fromstring(html_escape(kwargs["xml"])), {})
    return {"sent_xml": kwargs["xml"], "received_xml": response.content, "object": None}

def html_escape(xml_str):
    params  = re.search('<header>(.*)<\/header>',xml_str,re.S)
    replace = xml_str.replace(params.group(1),html.escape(params.group(1)))
    params2  = re.search('<parameters>(.*)<\/parameters>',replace,re.S)
    replace2 = replace.replace(params2.group(1),html.escape(params2.group(1)))
    return replace2.replace('&amp;','&')

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
