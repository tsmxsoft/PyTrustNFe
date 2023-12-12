# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import os
import requests
from lxml import etree
from .patch import has_patch
from .assinatura import Assinatura
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.utils import gerar_chave_cte, ChaveCTe
from pytrustnfe.Servidores import localizar_url
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from requests.packages.urllib3.exceptions import InsecureRequestWarning


# Zeep
from requests import Session
from zeep import Client
from zeep.transports import Transport


def _generate_cte_id(**kwargs):
    for item in kwargs["CTes"]:
        vals = {
            "cnpj": item["infCte"]["emit"]["cnpj_cpf"],
            "estado": item["infCte"]["ide"]["cUF"],
            "emissao": "%s%s"
            % (
                item["infCte"]["ide"]["dhEmi"][2:4],
                item["infCte"]["ide"]["dhEmi"][5:7],
            ),
            "modelo": item["infCte"]["ide"]["mod"],
            "serie": item["infCte"]["ide"]["serie"],
            "numero": item["infCte"]["ide"]["nCT"],
            "tipo": item["infCte"]["ide"]["tpEmis"],
            "codigo": item["infCte"]["ide"]["cCT"],
        }
        chave_cte = ChaveCTe(**vals)
        chave_cte = gerar_chave_cte(chave_cte, "CTe")
        item["infCte"]["ide"]["cCT"] = chave_cte
        item["infCte"]["ide"]["cDV"] = chave_cte[len(chave_cte) - 1:]


def _generate_cte_natural(**kwargs):
    return "%s%s%s%s%s%s" % (
        kwargs["CTe"]["infCte"]["ide"]["cUF"],
        kwargs["CTe"]["infCte"]["emit"]["cnpj_cpf"],
        kwargs["CTe"]["infCte"]["ide"]["serie"],
        kwargs["CTe"]["infCte"]["ide"]["nCT"],
        kwargs["CTe"]["infCte"]["ide"]["mod"],
        kwargs["CTe"]["infCte"]["ide"]["tpEmis"])


def _render(certificado, method, sign, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    xmlElem_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    modelo = xmlElem_send.find(".//{http://www.portalfiscal.inf.br/cte}mod")
    modelo = modelo.text if modelo is not None else "57"

    if sign:
        signer = Assinatura(certificado.pfx, certificado.password)
        if method == "CTeRecepcaoSincV4":
            xml_send = signer.assina_xml(
                xmlElem_send, kwargs["CTes"][0]["infCTe"]["Id"]
            )
    else:
        xml_send = etree.tostring(xmlElem_send, encoding=str)
    return xml_send


def _get_session(certificado):
    cert, key = extract_cert_and_key_from_pfx(
        certificado.pfx, certificado.password)
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
    transport = Transport(session=session)
    first_op, client = _get_client(base_url, transport)
    return _send_zeep(first_op, client, xml_send)


def _send_zeep(first_operation, client, xml_send):
    parser = etree.XMLParser(strip_cdata=False)
    xml = etree.fromstring(xml_send, parser=parser)

    namespaceNFe = xml.find(".//{http://www.portalfiscal.inf.br/cte}CTe")
    if namespaceNFe is not None:
        namespaceNFe.set("xmlns", "http://www.portalfiscal.inf.br/cte")

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    with client.settings(raw_response=True):
        response = client.service[first_operation](xml)
        response, obj = sanitize_response(response.text)
        return {
            "sent_xml": xml_send,
            "received_xml": response,
            "object": obj.Body.getchildren()[0],
        }


def xml_recepcionar_cte_v4(certificado, **kwargs):
    _generate_cte_id(**kwargs)
    return _render(certificado, "CTeRecepcaoSincV4", True, **kwargs)


def recepcionar_cte_v4(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_cte_v4(certificado, **kwargs)
    return _send(certificado, "CTeRecepcaoSincV4", **kwargs)
