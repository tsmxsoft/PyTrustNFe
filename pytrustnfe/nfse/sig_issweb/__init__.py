# -*- coding: utf-8 -*-
import requests
from pytrustnfe.xml import render_xml, sanitize_response
from lxml import etree
import sys
import os


def get_token(base_url, credenciais):
    url = base_url + '/login'

    response = requests.post(url, json=credenciais)
    if response.status_code == 200:
        return response.content
    
    raise Exception(response.text.encode('utf-8') or "Erro ao gerar token")


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    xml_string_send = render_xml(path, "%s.xml" % method, True, False, **kwargs)

    print(xml_string_send)
    return xml_string_send


def _send(certificado, method, **kwargs):

    base_url = kwargs.get("base_url", None)
    usuario = kwargs.get("usuario")
    senha = kwargs.get("senha")
    url = None
    metodo = None

    if not usuario or not senha:
        usuario = kwargs.get("nfse", {}).get("usuario", None)
        senha = kwargs.get("nfse", {}).get("senha", None)

    if not usuario or not senha:
        raise ValueError("Usuário e senha são obrigatórios para envio do XML.")

    xml_send = kwargs.get("xml", "")

    if not kwargs.get("base_url", None):
        if kwargs.get("ambiente", None) == "homologacao":
            base_url = "https://wshml2.sigissweb.com/rest"
        elif kwargs.get("ambiente", None) == "producao":
            base_url = "https://wsleme.sigissweb.com/rest"
    else:
        base_url = kwargs.get("base_url", None)

    if not base_url:
        raise ValueError("URL é obrigatória para envio do XML.")

    token = get_token(base_url, {"login": usuario, "senha": senha})

    headers = {
        "Authorization": token,
        "Content-Type": "application/xml"
    }

    if method == "GerarNfse":
        url = base_url + "/nfes"
        metodo = "post"
    elif method == "ConsultarNfse":
        metodo = "get"
        url = base_url + "/nfes/pegaxml/%s/serierps/%s" % (kwargs.get("nfse", {}).get("rps", {}).get("numero"),
                                                           kwargs.get("nfse", {}).get("rps", {}).get("serie"))

    req = requests.request(metodo, url, headers=headers, data=xml_send)

    if req.status_code == 200:
        response, obj = sanitize_response(req.text)
        return {"sent_xml": xml_send, "received_xml": response, "object": obj}
    
    return {"sent_xml": xml_send, "received_xml": req.text}


def consultar_nfse_por_rps(certificado, **kwargs):
    response = _send(certificado, "ConsultarNfse", **kwargs)
    xml = None

    try:
        xml_obj = response["object"]
        xml = etree.tostring(xml_obj, pretty_print=True)

        if sys.version_info[0] > 2:
            from html.parser import HTMLParser
            xml = xml.encode(str)
        else:
            from HTMLParser import HTMLParser
            xml = xml.encode('utf-8','ignore')
        
        xml = HTMLParser().unescape(xml)
    except:
        pass

    return xml


def xml_gerar_nfse(certificado, **kwargs):
    return _render(certificado, "GerarNfse", **kwargs)

def gerar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_gerar_nfse(certificado, **kwargs)
    return _send(certificado, "GerarNfse", **kwargs)

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return [xml_gerar_nfse(certificado, rps=x, **kwargs) for x in kwargs["nfse"]["lista_rps"]]

def recepcionar_lote_rps(certificado=None, **kwargs):
    lote = kwargs.get('nfse')
    ret = []
    for rps in lote["lista_rps"]:
        ret.append(str(gerar_nfse(certificado, **{
            "base_url": kwargs.get("base_url"),
            "rps": rps,
            "ambiente": kwargs.get("ambiente"),
            "usuario": rps.get("usuario"),
            "senha": lote.get("chave_digital"),
        })))
    return "\n\n".join(ret)

