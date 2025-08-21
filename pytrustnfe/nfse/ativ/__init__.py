# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import sys
from pytrustnfe.xml import render_xml, sanitize_response
from lxml import etree
import requests
import hashlib

def formatar_cep(cep):
    cep = str(cep)
    if len(cep) == 8:
        return "{}.{}-{}".format(cep[:2], cep[2:5], cep[5:])
    return cep

def formatar_rps(rps):
    rps = str(rps)
    rps = rps.zfill(12)
    return "{}-{}-{}".format(rps[:4], rps[4:8], rps[8:12])


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")


    usuario = kwargs.get('nfse', {}).get('lista_rps', [{}])[0].get('usuario', None)
    senha = kwargs.get('nfse', {}).get('lista_rps', [{}])[0].get('senha', None)
    
    if usuario is None and senha is None:
        usuario = kwargs.get('nfse', {}).get('usuario', None)
        senha = kwargs.get('nfse', {}).get('senha', None)

    if method == "RecepcionarLoteRps":
        kwargs["nfse"]["operacao"] = "1"
        for rps in kwargs.get("nfse", {}).get("lista_rps", []):
            if "cep" in rps.get("tomador", {}):
                rps["tomador"]["cep"] = formatar_cep(rps["tomador"]["cep"])
            if "numero" in rps:
                rps["numero"] = formatar_rps(rps["numero"])

    elif method in ["ConsultarNfsePorRps", "CancelarNfse"]:
        kwargs["nfse"]["operacao"] = "2" if method == "CancelarNfse" else "3"
        kwargs["nfse"]["rps"]["numero"] = formatar_rps(kwargs["nfse"]["rps"]["numero"])


    usuario = kwargs.get('nfse', {}).get('usuario', None)
    senha = kwargs.get('nfse', {}).get('senha', None)

    nfse_competencia = kwargs.get('nfse', {}).get('lista_rps', [{}])[0].get('data_competencia', None)

    if not usuario or not senha:
        raise ValueError("Usuário e senha são obrigatórios para autenticação")

    kwargs["nfse"]["nfse_data_competencia"] = nfse_competencia

    kwargs["nfse"]["usuario"] = usuario

    tipo_rps = kwargs.get('nfse', {}).get('lista_rps', [{}])[0].get('tipo_rps', None)
    kwargs["nfse"]["tipo_rps"] = tipo_rps

    senha_md5 = hashlib.md5(senha.encode('utf-8')).hexdigest()
    kwargs["nfse"]["senha"] = senha_md5

    xml_string_send = render_xml(path, "%s.xml" % method, True, False, **kwargs)
    
    print(xml_string_send)

    return xml_string_send


def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")

    base_url = kwargs.get("base_url", None)
    
    if not base_url:
        raise ValueError("Necessário informar URL de produção")

    
    xml_send = kwargs["xml"]

    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, False, **{"soap_body":xml_send, "method": method, "nfse": kwargs.get("nfse", {})})

    
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "",
        "Content-length": str(len(soap))
    }


    request = requests.post(base_url, data=soap, headers=headers)
    response, obj = sanitize_response(request.content.decode('utf8', 'ignore'))    
    try:
        return {"sent_xml": str(soap), "received_xml": str(response.encode('utf8')), "object": obj.Body }
    except:
        return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }
    



def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRps", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRps", **kwargs)




def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    response = _send(certificado, "CancelarNfse", **kwargs)

    return response




def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarLoteRps", **kwargs)
    xml = None

    try:
        res, xml_obj = sanitize_response(response['object']['ConsultarLoteRpsResponse']['outputXML'].text)
        xml = etree.tostring(xml_obj,xml_declaration=False)
        if sys.version_info[0] > 2:
            from html.parser import HTMLParser
            xml = xml.encode(str)
        else:
            from HTMLParser import HTMLParser
            xml = xml.encode('utf-8','ignore')
        #unescape
        xml = HTMLParser().unescape(xml)
    except:
        pass

    return xml




def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfsePorRps", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
    xml = None
    res, xml_obj = sanitize_response(response['received_xml'])
    try:
        #Conversão de volta a string
        xml = etree.tostring(xml_obj)
        if sys.version_info[0] > 2:
            from html.parser import HTMLParser
            xml = xml.encode(str)
        else:
            from HTMLParser import HTMLParser
            xml = xml.encode('utf-8','ignore')
        #unescape
        xml = HTMLParser().unescape(xml)
    except:
        pass
    
    return xml
