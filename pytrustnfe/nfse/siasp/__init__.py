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

    xml_signed_send = signer.assina_xml(xml_send, None)

    return xml_signed_send



def _send(certificado, method, **kwargs):
    base_url = ""
    if kwargs["ambiente"] == "homologacao":
        base_url = "http://nfse-teste.publica.inf.br/homologa_nfse_integracao/Services?wsdl"
    elif "base_url" in kwargs:
        base_url = kwargs["base_url"]
    else:
        #caso nenhum selecionado, escolher Assú/RN
        base_url = "https://nfse-assu.e-publica.net/assu_nfse_integracao/Services?wsdl"

    cert, key = extract_cert_and_key_from_pfx(
        certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    client = Client(wsdl=base_url, transport=transport)

    response = client.service[method](kwargs["xml"])
    response, obj = sanitize_response(response)
    return {"sent_xml": kwargs["xml"], "received_xml": response, "object": obj}


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
