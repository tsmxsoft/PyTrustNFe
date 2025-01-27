# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.webiss.assinatura import Assinatura
from lxml import etree
from zeep import Client
from zeep.transports import Transport
from requests import Session
import requests
from datetime import datetime, timedelta


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )

    xml_string_send = render_xml(path, "%s.xml" % method, True, False, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    return etree.tostring(xml_send)

def _send(certificado, method, **kwargs):
    url = kwargs["base_url"]

    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, False, **{"soap_body":xml_send, "method": method })

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    action = "http://www.nfe.com.br/%s" %(method)
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": action,
        "Operation": method,
        "Content-length": str(len(soap))
    }
    request = requests.post(url, data=soap, headers=headers, cert=(cert,key))
    response, obj = sanitize_response(request.content.decode('utf8', 'ignore'))
    return {"sent_xml": str(soap), "received_xml": str(response.encode('utf8')), "object": obj.Body }

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRps", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRps", **kwargs)

def gerar_nfse(certificado, **kwargs):
    return _send(certificado, "GerarNfse", **kwargs)


def envio_lote_rps_assincrono(certificado, **kwargs):
    return _send(certificado, "RecepcionarLoteRps", **kwargs)


def envio_lote_rps(certificado, **kwargs):
    return _send(certificado, "RecepcionarLoteRpsSincrono", **kwargs)


def cancelar_nfse(certificado, **kwargs):
    return _send(certificado, "CancelarNfse", **kwargs)


def substituir_nfse(certificado, **kwargs):
    return _send(certificado, "SubstituirNfse", **kwargs)


def consulta_situacao_lote_rps(certificado, **kwargs):
    return _send(certificado, "ConsultaSituacaoLoteRPS", **kwargs)


def consulta_nfse_por_rps(certificado, **kwargs):
    return _send(certificado, "ConsultaNfsePorRps", **kwargs)


def consultar_lote_rps(certificado, **kwargs):
    return _send(certificado, "ConsultarLoteRps", **kwargs)


def consulta_nfse_servico_prestado(certificado, **kwargs):
    return _send(certificado, "ConsultarNfseServicoPrestado", **kwargs)


def consultar_nfse_servico_tomado(certificado, **kwargs):
    return _send(certificado, "ConsultarNfseServicoTomado", **kwargs)


def consulta_nfse_faixe(certificado, **kwargs):
    return _send(certificado, "ConsultarNfseFaixa", **kwargs)


def consulta_cnpj(certificado, **kwargs):
    return _send(certificado, "ConsultaCNPJ", **kwargs)