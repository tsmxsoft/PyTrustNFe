# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import os
import sys
from decimal import Decimal
import requests
from lxml import etree
from requests import Session
from pytrustnfe.nfse.nfpaulistana.assinatura import Assinatura
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key


op2action = {
    "TesteEnvioLoteRPSAsync": "http://www.prefeitura.sp.gov.br/nfe/ws/testeEnvioLoteRPSAsync",
    "EnvioLoteRPSAsync": "http://www.prefeitura.sp.gov.br/nfe/ws/envioLoteRPSAsync",
}

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=True
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    referencia = ""
    if method == "EnvioLoteRPS":
        kwargs["nfse"]["total_servicos"] = sum(Decimal(rps["servico"]["valor_servico"]) for rps in kwargs["nfse"]["lista_rps"] if "valor_servico" in rps["servico"]) or Decimal("0.00")
        kwargs["nfse"]["total_deducoes"] = sum(Decimal(rps["servico"]["deducoes"]) for rps in kwargs["nfse"]["lista_rps"] if "deducoes" in rps["servico"]) or Decimal("0.00")

        for i, rps in enumerate(kwargs['nfse']['lista_rps']):
            kwargs['nfse']['lista_rps'][i]['status'] = "N" if rps['status'] == "1" else "C"
            kwargs['nfse']['lista_rps'][i]['servico']['iss_retido'] = "S" if rps['servico']['iss_retido'] == "1" else "N"


    xml_string_send = render_xml(path, "%s.xml" % method, True, True, **kwargs)
    xml_string_send = re.sub(r'[\r\n]','',xml_string_send)
    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    if method == "EnvioLoteRPS":
        #Assina os RPS
        signer.gerar_assinatura_rps(xml_send,**kwargs)
        #Assina o lote
        xml_signed_send = signer.assina_xml(xml_send)
    else:
        xml_signed_send = etree.tostring(xml_send)

    xml_signed_send = re.sub(r'[\r\n]','',xml_signed_send)
    print ('--- xml ---')
    print (xml_signed_send)

    return xml_signed_send

def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")

    url = kwargs["base_url"]

    if method == "EnvioLoteRPS" and kwargs.get("ambiente", "producao") == "homologacao":
        method = "TesteEnvioLoteRPS"

    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", True, True, **{"soap_body":xml_send, "method": method })

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    session = Session()
    session.cert = (cert, key)
    op = "%sAsync" %(method)
    if method == "ConsultaSituacaoLote":
        op = method
    action = op2action[op]
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": action,
        "Operation": op,
        "Content-length": str(len(soap))
    }
    request = session.post(url, data=soap, headers=headers)
    print(request.content)
    response, obj = sanitize_response(request.content.decode('utf8', 'ignore'))
    try:
        return {"sent_xml": str(soap), "received_xml": str(response.encode('utf8')), "object": obj.Body }
    except:
        return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "EnvioLoteRPS", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    kwargs["base_url"] = "https://nfews.prefeitura.sp.gov.br/lotenfeasync.asmx"
    return _send(certificado, "EnvioLoteRPS", **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "cancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    response = _send(certificado, "cancelarNfse", **kwargs)
    xml = None

    try:
        #Conversão a objeto e Busca pelo elemento Nfse
        res, xml_obj = sanitize_response(response['object']['cancelarNfseResponse']['return'].text)
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
    return _render(certificado, "ConsultaSituacaoLote", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    kwargs["base_url"] = "https://nfews.prefeitura.sp.gov.br/lotenfeasync.asmx"
    response = _send(certificado, "ConsultaSituacaoLote", **kwargs)
    xml = None

    try:
        xml_clean = re.sub(r'\<\?xml.+\?\>\n?','',response['object']['RetornoConsultaSituacaoLote'])
        res, xml_obj = sanitize_response(xml_clean)
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
