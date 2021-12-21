# coding=utf-8
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import requests
from pytrustnfe.xml import render_xml
from lxml import etree


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    # xml string
    etree.fromstring(xml_string_send, parser=parser)

    return xml_string_send


def _send(certificado, method, **kwargs):
    base_url = "https://agiliblue.agilicloud.com.br/api/" + method
    headers = {'Content-Type': 'application/xml'}
    
    resp = requests.post(base_url, data=kwargs['xml'], headers=headers)
    return {"sent_xml": kwargs['xml'], "received_xml": resp.text, "object": None}


def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "EnviarLoteRps", **kwargs)


def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "EnviarLoteRps", **kwargs)


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