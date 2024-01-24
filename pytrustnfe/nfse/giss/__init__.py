# -*- coding: utf-8 -*-
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os

from requests import Session

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.siasp.assinatura import Assinatura
from lxml import etree
from requests.packages.urllib3 import disable_warnings
from zeep import Client
from zeep.transports import Transport
import requests

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(remove_blank_text=True, 
                             remove_comments=True, 
                             strip_cdata=False)

    signer = Assinatura(certificado.pfx, certificado.password)
    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)
    xml_send = etree.fromstring(xml_string_send, parser=parser)
    xml_signed_send = signer.assina_xml(xml_send)

    return xml_signed_send

def _send(certificado, method, **kwargs):
    base_url = ""
    
    if kwargs["ambiente"] == "homologacao":
        base_url = "https://homologacao.ginfes.com.br/ServiceGinfesImpl?wsdl"
    else:
        base_url = "https://producao.ginfes.com.br/ServiceGinfesImpl?wsdl"

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    client = Client(wsdl=base_url, transport=transport)

    xml_send = {}
    xml_send = {
        "arg0": """<ns1:cabecalho xmlns:ns1="http://www.ginfes.com.br/cabecalho_v03.xsd" versao="3">
            <versaoDados>3</versaoDados>
            </ns1:cabecalho>""",
        "arg1": kwargs["xml"],
    }
    
    try:
        response = client.service[method](**xml_send)
        response, obj = sanitize_response(response)
    except Exception as e:
        response = str(e)
        obj = None

    return {"sent_xml": xml_send, "received_xml": response, "object": obj}

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRpsV3", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRpsV3", **kwargs)

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRpsV3", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, "ConsultarLoteRpsV3", **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "CancelarNfse", **kwargs)
