# -*- coding: utf-8 -*-
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os

from requests import Session

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.siasp.assinatura import Assinatura
from lxml import etree
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
        base_url = "https://isshomo.sefin.fortaleza.ce.gov.br/grpfor-iss/ServiceGinfesImplService"
    else:
        base_url = "https://iss.fortaleza.ce.gov.br/grpfor-iss/ServiceGinfesImplService"

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    xml_send = kwargs["xml"]
    op = method
    if method == "RecepcionarLoteRpsV3":
        op = "EnviarLoteRpsEnvio"
    elif method == "ConsultarLoteRpsV3":
        op = "ConsultarLoteRpsEnvio"
    elif method == "CancelarNfse":
        op = "CancelarNfseEnvio"
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, **{"soap_body":xml_send, "method": method, "op": op})

    session = Session()
    session.cert = (cert, key)
    session.verify = False
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "Content-length": str(len(soap))
    }

    request = requests.post(base_url, data=soap, headers=headers,verify=False,cert=(cert, key))
    try:
        response, obj = sanitize_response(request.content.decode('utf8', 'ignore'))
    except Exception as e:
        return {"sent_xml": str(soap), "received_xml": str(e), "object": None}

    return {"sent_xml": str(soap), "received_xml": str(response.encode('utf8')), "object": obj.Body }

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
