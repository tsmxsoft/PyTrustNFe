# -*- coding: utf-8 -*-
# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from lxml import etree
from requests import Session
from zeep import Client
from zeep.transports import Transport

from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.nfse.megasoft.assinatura import Assinatura


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    xml_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    reference = ""
    if method == "GerarNfse":
        reference = "rps:%s%s" % (str(kwargs["rps"]["numero"]),str(kwargs["rps"]["serie"]))
    elif method == "CancelarNfse":
        reference = "nfse:%s" % str(kwargs["nfse"]["rps"]["numero"])

    signer = Assinatura(certificado.pfx, certificado.password)
    xml_send = signer.assina_xml(etree.fromstring(xml_send), reference)
    return xml_send.encode("utf-8")


def _send(certificado, method, **kwargs):
    base_url = kwargs.get("base_url")

    xml_send = kwargs["xml"].decode("utf-8")
    xml_cabecalho = '<cabecalho xmlns="http://megasoftarrecadanet.com.br/xsd/nfse_v01.xsd" versao="1.00">\
    <versaoDados>1.00</versaoDados>\
</cabecalho>'

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    client = Client(base_url, transport=transport)

    print(xml_send)
    response = client.service[method](xml_cabecalho, xml_send)

    response, obj = sanitize_response(response)
    return {"sent_xml": xml_send, "received_xml": response, "object": obj}


def xml_gerar_nfse(certificado, **kwargs):
    return _render(certificado, "GerarNfse", **kwargs)


def gerar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_gerar_nfse(certificado, **kwargs)
    return _send(certificado, "GerarNfse", **kwargs)


def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)


def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "CancelarNfse", **kwargs)


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