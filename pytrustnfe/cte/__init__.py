# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import os
import sys
import requests
from lxml import etree
from .assinatura import Assinatura
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.utils import gerar_chave_cte, ChaveCTe
from pytrustnfe.Servidores import localizar_url, ESTADO_WS, SIGLA_ESTADO, SVRS
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pytrustnfe import get_version

#Crypto
from OpenSSL import crypto
from base64 import b64encode

# Zeep
from requests import Session
from zeep import Client
from zeep.transports import Transport


def _generate_cte_id(certificado,**kwargs):
    cte = kwargs["CTe"]
    vals = {
        "cnpj": cte["infCte"]["emit"]["cnpj_cpf"],
        "estado": cte["infCte"]["ide"]["cUF"],
        "emissao": "%s%s"
        % (
            cte["infCte"]["ide"]["dhEmi"][2:4],
            cte["infCte"]["ide"]["dhEmi"][5:7],
        ),
        "modelo": cte["infCte"]["ide"]["mod"],
        "serie": cte["infCte"]["ide"]["serie"],
        "numero": cte["infCte"]["ide"]["nCT"],
        "tipo": cte["infCte"]["ide"]["tpEmis"],
        "codigo": cte["infCte"]["ide"]["cCT"],
    }
    chave_cte = ChaveCTe(**vals)
    chave_cte = gerar_chave_cte(chave_cte, "CTe")

    cte["infCte"]["Id"] = chave_cte
    cte["infCte"]["ide"]["cDV"] = chave_cte[len(chave_cte) - 1:]
    cte["infCte"]["ide"]["verProc"] = "PyTrustNFe" + get_version()

    cte["infCTeSupl"] = {}
    ws = ESTADO_WS[SIGLA_ESTADO[kwargs["estado"]]]
    cte["infCTeSupl"]["qrCodCTe"] = \
        ws[kwargs["modelo"]][kwargs["ambiente"]]["QRCode"] \
    + "?chCTe=%s&amp;tpAmb=%s" %(chave_cte[3:],cte["infCte"]["ide"]["tpAmb"])
    #Contingencia
    if cte["infCte"]["ide"]["tpEmis"] == 2 or cte["infCte"]["ide"]["tpEmis"] == 5:
        cte["infCTeSupl"]["qrCodCTe"] += "&amp;sign=%s" %_sign_rsa(certificado,chave_cte[3:])


def _sign_rsa(certificado, data):
    pfx = crypto.load_pkcs12(certificado.pfx, certificado.password)
    signed = crypto.sign(pfx.get_privatekey(),data,"sha1")
    return b64encode(signed)


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
    xml_send = render_xml(path, "%s.xml" % method, True, **kwargs)
    
    if sign:
        signer = Assinatura(certificado.pfx, certificado.password)
        if method == "CTeRecepcaoSincV4":
            xml_send = signer.assina_xml(
                etree.fromstring(xml_send), kwargs["CTe"]["infCte"]["Id"]
            )
    
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

    namespaceCTe = xml.find(".//{http://www.portalfiscal.inf.br/cte}CTe")
    if namespaceCTe is not None:
        namespaceCTe.set("xmlns", "http://www.portalfiscal.inf.br/cte")

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
    _generate_cte_id(certificado,**kwargs)
    return _render(certificado, "CTeRecepcaoSincV4", True, **kwargs)


def recepcionar_cte_v4(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_cte_v4(certificado, **kwargs)
    return _send(certificado, "CTeRecepcaoSincV4", **kwargs)


def xml_consulta_cte_v4(certificado, **kwargs):
    return _render(certificado, "CTeConsultaV4", False, **kwargs)


def consulta_cte_v4(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consulta_cte_v4(certificado,**kwargs)
        kwargs["modelo"] = "57"
    return _send(certificado, "CTeConsultaV4", **kwargs)


def xml_status_servico_cte_v4(certificado, **kwargs):
    return _render(certificado, "CTeStatusServicoV4", False, **kwargs)


def status_servico_cte_v4(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_status_servico_cte_v4(certificado,**kwargs)
        kwargs["modelo"] = "57"
    return _send(certificado, "CTeStatusServicoV4", **kwargs)