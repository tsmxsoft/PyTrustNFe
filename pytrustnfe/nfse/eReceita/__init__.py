# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import os
import sys
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.eReceita.assinatura import Assinatura
from lxml import etree
from requests import Session
import requests



def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    xml_string_send = render_xml(path, "%s.xml" % method, True, False, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)
    

    if method == "RecepcionarLoteRps":
        referencia = kwargs.get('nfse').get('numero_lote')
        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps{0}{1}".format(
                item.get('numero'), item.get('serie'))

            signer.assina_xml(xml_send, reference)

        xml_signed_send = signer.assina_xml(xml_send, "lote{0}".format(referencia))
        

    elif method == "CancelarNfse":
        xml_signed_send = signer.assina_xml(xml_send, '{0}'.format(kwargs.get('nfse').get('numero')))
    
    else:
        print('--- xml ---')
        print(xml_string_send)
        return xml_string_send

    
    print('--- xml ---')
    print(xml_signed_send)
    return xml_signed_send

def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")

    base_url = kwargs.get("base_url", None)
    ambiente = kwargs.get("ambiente", None)
    action = ""

    # Se informar ambiente e não informar base_url, usar como padrão URL de Monte Carmelo - MG
    if ambiente == "homologacao" and not base_url:
        base_url = "https://www3.ereceita.net.br/ws/montecarmelomg/wsHomologacao.php"
        action = "https://www3.ereceita.net.br/%s" % (method)
    elif ambiente == "producao" and not base_url:
        action = "https://www.ereceita.net.br/%s" % (method)
        base_url = "https://webservice.ereceita.net.br/ws/montecarmelomg/wsProducao.php"
    else:
        action = "https://www.ereceita.net.br/%s" % (method)
    
    if not base_url:
        raise ValueError("Informar URL de produção")

    
    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, False, **{"soap_body":xml_send, "method": method })

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": action,
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

def xml_recepcionar_lote_rps_sincrono(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRpsSincrono", **kwargs)


def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    response = _send(certificado, "CancelarNfse", **kwargs)
    xml = None

    try:
        #Conversão a objeto e Busca pelo elemento Nfse
        res, xml_obj = sanitize_response(response["object"]["CancelarNfseResponse"]['outputXML'].text)
        #Caso haja algum erro, as mensagens serão retornadas
        if xml_obj.find(".//ListaMensagemRetorno") is not None:
            xml_obj = xml_obj.find(".//ListaMensagemRetorno")
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
    except Exception as err:
        pass

    return xml

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

def substituir_nfse(certificado, **kwargs):
    return _send(certificado, "SubstituirNfse", **kwargs)

def consulta_situacao_lote_rps(certificado, **kwargs):
    return _send(certificado, "ConsultaSituacaoLoteRPS", **kwargs)

def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfsePorRps", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
    xml = None
    try:
        res, xml_obj = sanitize_response(response["object"]["ConsultarNfsePorRpsResponse"]['outputXML'].text)
        if xml_obj.find(".//CompNfse"):
            xml_obj = xml_obj.find(".//CompNfse")
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
