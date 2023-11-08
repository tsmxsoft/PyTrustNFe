# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# Endereços Simpliss Piracicaba
# Homologação: http://wshomologacao.simplissweb.com.br/nfseservice.svc
# Homologação site: http://homologacaonovo.simplissweb.com.br/Account/Login

# Prod:http://sistemas.pmp.sp.gov.br/semfi/simpliss/contrib/Account/Login
# Prod:http://sistemas.pmp.sp.gov.br/semfi/simpliss/ws_nfse/nfseservice.svc

import os
from lxml import etree
from requests import Session
from zeep.transports import Transport
from pytrustnfe.xml import render_xml, sanitize_response

from zeep import Client, Settings, xsd
from datetime import datetime, timedelta
import requests 

def _render_xml(certificado, method, **kwargs):
    kwargs['method'] = method
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    return etree.tostring(xml_send)

def _send(certificado, method, **kwargs):
    if kwargs["ambiente"] == "producao":
        base_url = "https://nfsebrasil.net.br"
    else:
        base_url = "https://web1.memory.com.br"

    xml_send = ""
    if "xml" in kwargs:
        xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    params = {
        "soap_body":xml_send, 
        "method": method,
        "cod_mun": kwargs["nfse"]["lista_rps"][0]["servico"]["codigo_municipio"],
        "chave_prestador": kwargs["nfse"]["chave_digital"],
        "cnpj_prestador": kwargs["nfse"]["cnpj_prestador"]
    }
    if method == "consultarLoteRPS":
        params["protocolo"] = kwargs["nfse"]["protocolo"]
    elif method == "cancelarNFSE":
        params["numeroNFSE"] = kwargs["nfse"]["numero_nfse"]
    soap = render_xml(path, "SoapRequest.xml", False, **params)

    action = "urn:loterpswsdl#tm_lote_rps_service." + method
    headers = {
        "User-Agent": "PyTrustNFE3",
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": action,
        "Content-length": str(len(soap))
    }

    request = requests.post(base_url + '/nfse/ws/lote_rps_service.php', data=soap, headers=headers)
    try:
        response, obj = sanitize_response(request.content)
    except Exception as e:
        return {"sent_xml": str(soap), "received_xml": request.content, "object": None}
    return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render_xml(certificado, "importarLoteRPS", **kwargs)


def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado,"importarLoteRPS", **kwargs)


def xml_consultar_situacao_lote(certificado, **kwargs):
    return _render_xml(certificado, "ConsultarSituacaoLoteRps", **kwargs)


def consultar_situacao_lote(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_situacao_lote(certificado, **kwargs)
    return _send(None, "ConsultarSituacaoLoteRps", **kwargs)


def consultar_nfse_por_rps(certificado, **kwargs):
    return _send(None, "ConsultarNfsePorRps", **kwargs)


def consultar_lote_rps(certificado, **kwargs):
    return _send(certificado, "consultarLoteRPS", **kwargs)


def xml_consultar_nfse(certificado, **kwargs):
    return _render_xml(certificado, "ConsultarNfse", **kwargs)


def consultar_nfse(certificado, **kwargs):
    return _send("ConsultarNfse", **kwargs)


def cancelar_nfse(certificado, **kwargs):
    return _send(certificado, "cancelarNFSE", **kwargs)


def xml_gerar_nfse(certificado, **kwargs):
    return _render_xml(certificado, "GerarNfse", **kwargs)


def gerar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send("GerarNfse", **kwargs)
