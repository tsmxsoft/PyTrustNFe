# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import os
import sys
import requests
from hashlib import sha512
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from requests import Session
from lxml import etree
import base64
import traceback

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)
    
    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)
    

    if method == "GerarNfse":
        rps_xml_object = xml_send.find(".//{http://www.abrasf.org.br/nfse.xsd}Rps")
        rps_xml_string = etree.tostring(rps_xml_object, encoding='unicode')
        token = kwargs.get("chave_digital")

    elif method == "ConsultarNfsePorRps":
        rps_xml_object = xml_send.find(".//{http://www.abrasf.org.br/nfse.xsd}IdentificacaoRps")
        rps_xml_object_prestador = xml_send.find(".//{http://www.abrasf.org.br/nfse.xsd}Prestador")

        rps_xml_string = etree.tostring(rps_xml_object, encoding='unicode')
        token = kwargs.get("nfse").get("chave_digital")
        prestador_xml_string = etree.tostring(rps_xml_object_prestador, encoding='unicode')
        rps_xml_string = rps_xml_string + prestador_xml_string

    rps_xml_string = re.sub(r'\sxmlns="[^"]+"', '', rps_xml_string)
    
    if not token:
        raise ValueError("Chave digital não encontrada. Obrigatória para geração do RPS.")
    
    tag = re.sub(r'[^\x20-\x7E]+', '', rps_xml_string)
    tag = re.sub(r'[ ]+', '', tag)
    
    integridade = sha512(tag + token).hexdigest()

    if integridade:
        try:
            kwargs['rps']['integridade'] = integridade
        except:
            kwargs['nfse']['rps']['integridade'] = integridade

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)


    xml_signed_send = etree.tostring(xml_send)
    print(xml_signed_send)

    return xml_signed_send

def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")

    if kwargs["ambiente"] == "homologacao":
        url = "https://limeira.iibrasil.com.br/api/soap/homologacao_notafiscal.php?wsdl"
    elif kwargs["ambiente"] == "producao":
        url = "https://limeira.iibrasil.com.br/api/soap/notafiscal.php?wsdl"

    
    xml_send = kwargs["xml"]

    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, False, soap_body=xml_send, method=method)
    

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    session = Session()
    session.cert = (cert, key)
    session.verify = False

    action = "http://nfse.abrasf.org.br/%s" %(method)
    
    headers = {
        "SOAPAction": action,
        "Content-length": str(len(soap)),
        'Content-Type': 'text/xml; charset=utf-8'
    }

    # request = requests.post(url, data=soap, cert=(cert, key), headers=headers)
    # response = request.content

    # response, obj = sanitize_response(request.content)
    # return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }



def xml_gerar_nfse(certificado, **kwargs):
    print('kwargs', kwargs)
    return _render(certificado, "GerarNfse", **kwargs)


def gerar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_gerar_nfse(certificado, **kwargs)
    return _send(certificado, "GerarNfse", **kwargs)


def xml_recepcionar_lote_rps(certificado, **kwargs):
    return [xml_gerar_nfse(certificado,rps=x,**kwargs) for x in kwargs["nfse"]["lista_rps"]]

def recepcionar_lote_rps(certificado = None, **kwargs):
    lote = kwargs.get('nfse')
    ret = []
    for rps in lote["lista_rps"]:
        ret.append(str(gerar_nfse(certificado,**{
            "base_url": kwargs.get("base_url"),
            "rps": rps,
            "chave_digital": lote.get("chave_digital"),
            "ambiente": kwargs.get("ambiente")
        })))
    return "\n\n".join(ret)


def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfsePorRps", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
    xml = None

    try:
        link_nfse = None
        res, xml_obj = sanitize_response(
            response["object"]["ConsultarNfsePorRpsResponse"]['outputXML'].text)

        if xml_obj.find(".//ListaMensagemRetorno"):
            xml_obj = xml_obj.find(".//ListaMensagemRetorno")

        if xml_obj.find(".//LinkNfse"):
            link_nfse = xml_obj.find(".//LinkNfse").text
            link_decoded = base64.b64decode(link_nfse).decode('utf-8')

        xml = etree.tostring(xml_obj, pretty_print=True)

        if sys.version_info[0] > 2:
            from html.parser import HTMLParser
            xml = xml.encode(str)
        else:
            from HTMLParser import HTMLParser
            xml = xml.encode('utf-8','ignore')
        
        xml = HTMLParser().unescape(xml)
    except:
        traceback.print_exc()

    if link_nfse:
        return {"xml": xml, "link_nfse": link_decoded}
    
    return xml


