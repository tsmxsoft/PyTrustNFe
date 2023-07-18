# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import os
import requests
from lxml import etree
from .patch import has_patch
from .assinatura import Assinatura
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.utils import  gerar_chave_nfcom, ChaveNFCom
from pytrustnfe.Servidores import localizar_url
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Zeep
from requests import Session
from zeep import Client
from zeep.transports import Transport


def _generate_nfcom_id(**kwargs):
    item = kwargs.get("infNFCom")
    vals = {
        "cnpj": item["emit"]["cnpj_cpf"],
        "estado": item["ide"]["cUF"],
        "emissao": "%s%s"
        % (
            item["ide"]["dhEmi"][2:4],
            item["ide"]["dhEmi"][5:7],
        ),
        "modelo": item["ide"]["mod"],
        "serie": item["ide"]["serie"],
        "numero": item["ide"]["nNF"],
        "tipo": item["ide"]["tpEmis"],
        "codigo": item["ide"]["cNF"],
    }
    chave_nfcom = ChaveNFCom(**vals)
    chave_nfcom = gerar_chave_nfcom(chave_nfcom)
    item["Id"] = chave_nfcom
    item["ide"]["cDV"] = chave_nfcom[len(chave_nfcom) - 1 :]


def _render(certificado, method, sign, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    xmlElem_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    if sign:
        signer = Assinatura(certificado.pfx, certificado.password)
        if method == "NFComRecepcao":
            xml_send = signer.assina_xml(xmlElem_send, kwargs["infNFCom"]["Id"])

    else:
        xml_send = etree.tostring(xmlElem_send, encoding=str)
    return xml_send


def _get_session(certificado):
    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    session = Session()
    session.cert = (cert, key)
    session.verify = False
    return session


def _get_client(base_url, transport):
    client = Client(base_url, transport=transport)
    port = next(iter(client.wsdl.port_types))
    first_operation = [
        x
        for x in iter(client.wsdl.port_types[port].operations)
        if "zip" not in x.lower()
    ][0]
    return first_operation, client


def _send(certificado, method, **kwargs):
    xml_send = kwargs["xml"]
    base_url = localizar_url(
        method, kwargs["estado"], kwargs["modelo"], kwargs["ambiente"]
    )
    session = _get_session(certificado)
    patch = has_patch(kwargs["estado"], method)
    if patch:
        return patch(session, xml_send, kwargs["ambiente"])
    transport = Transport(session=session)
    first_op, client = _get_client(base_url, transport)
    return _send_zeep(first_op, client, xml_send)


def _send_zeep(first_operation, client, xml_send):
    parser = etree.XMLParser(strip_cdata=False)
    xml = etree.fromstring(xml_send, parser=parser)

    namespaceNFCom = xml.find(".//{http://www.portalfiscal.inf.br/NFCom}NFCom")
    if namespaceNFCom is not None:
        namespaceNFCom.set("xmlns", "http://www.portalfiscal.inf.br/NFCom")

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    with client.settings(raw_response=True):
        response = client.service[first_operation](xml)
        response, obj = sanitize_response(response.text)
        return {
            "sent_xml": xml_send,
            "received_xml": response,
            "object": obj.Body.getchildren()[0],
        }


def xml_autorizar_nfcom(certificado, **kwargs):
    _generate_nfcom_id(**kwargs)
    return _render(certificado, "NFComRecepcao", True, **kwargs)


def autorizar_nfcom(certificado, **kwargs):  # Assinar
    if "xml" not in kwargs:
        kwargs["xml"] = xml_autorizar_nfcom(certificado, **kwargs)
    return _send(certificado, "NFComRecepcao", **kwargs)