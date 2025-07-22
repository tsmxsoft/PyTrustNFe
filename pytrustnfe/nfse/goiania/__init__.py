# -*- coding: utf-8 -*-
# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.utils import conversao_codigo_sedetec
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.nfse.goiania.assinatura import Assinatura
from lxml import etree
import traceback
import requests
import sys
import os


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    municipio_servico = kwargs.get("rps", {}).get("prestador", {}).get("cidade", None)
    municipio_tomador = kwargs.get("rps", {}).get("tomador", {}).get("cidade", None)
    uf_tomador = kwargs.get("rps", {}).get("tomador", {}).get("uf", None)

    reference = ""
    if method == "GerarNfse":
        reference = "rps:%s%s" % (str(kwargs["rps"]["numero"]),str(kwargs["rps"]["serie"]))
        kwargs["rps"]["servico"]["codigo_municipio"] = conversao_codigo_sedetec(municipio_servico)
        kwargs["rps"]["tomador"]["codigo_municipio"] = conversao_codigo_sedetec(municipio_tomador, uf_tomador)

    xml_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    if reference:        
        signer = Assinatura(certificado.pfx, certificado.password)

        xml_send = etree.fromstring(xml_send)
        xml_send = signer.assina_xml(xml_send)

    return xml_send.encode("utf-8")


def _send(certificado, method, **kwargs):
    base_url = kwargs.get("base_url")

    if not base_url:
        base_url = "https://nfse.goiania.go.gov.br/ws/nfse.asmx?wsdl"

    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, False, **{"soap_body":xml_send, "method":method})

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    action = "http://nfse.goiania.go.gov.br/ws/%s" % method

    headers = {
        "SOAPAction": action,
        "Content-Type": "text/xml; charset=utf-8",
        "Content-length": str(len(soap)),
    }

    request = requests.post(base_url, data=soap, cert=(cert, key), headers=headers)
    response, obj = sanitize_response(request.content)

    return {"sent_xml": xml_send, "received_xml": response, "object": obj.Body}
    

def xml_gerar_nfse(certificado, **kwargs):
    return _render(certificado, "GerarNfse", **kwargs)


def gerar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_gerar_nfse(certificado, **kwargs)
    return _send(certificado, "GerarNfse", **kwargs)


def xml_recepcionar_lote_rps(certificado, **kwargs):
    return [xml_gerar_nfse(certificado,rps=x,**kwargs) for x in kwargs["nfse"]["lista_rps"]]

def recepcionar_lote_rps(certificado = None, **kwargs):
    lote = kwargs.get('nfse')
    ret = []
    for rps in lote["lista_rps"]:
        ret.append(str(gerar_nfse(certificado,**{
            "base_url": kwargs.get("base_url"),
            "rps": rps,
        })))
    return "\n\n".join(ret)


def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarNfseRps", **kwargs)
    xml = None

    try:
        xml_obj = response["object"]["ConsultarNfseRpsResponse"]

        if xml_obj.find(".//ListaMensagemRetorno"):
            xml_obj = xml_obj.find(".//ListaMensagemRetorno")

        xml = etree.tostring(xml_obj)
        if sys.version_info[0] > 2:
            from html.parser import HTMLParser
            xml = xml.encode(str)
        else:
            from HTMLParser import HTMLParser
            xml = xml.encode('utf-8','ignore')
        
        xml = HTMLParser().unescape(xml)
    except:
        traceback.print_exc()

    return xml


def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfseRps", **kwargs)
