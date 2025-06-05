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
    #Sync
    "CancelamentoNFe": "http://www.prefeitura.sp.gov.br/nfe/ws/cancelamentoNFe",
    "ConsultaCNPJ": "http://www.prefeitura.sp.gov.br/nfe/ws/consultaCNPJ",
    "ConsultaInformacoesLote": "http://www.prefeitura.sp.gov.br/nfe/ws/consultaInformacoesLote",
    "ConsultaLote": "http://www.prefeitura.sp.gov.br/nfe/ws/consultaLote",
    "ConsultaNFe": "http://www.prefeitura.sp.gov.br/nfe/ws/consultaNFe",
    "ConsultaNFeEmitidas": "http://www.prefeitura.sp.gov.br/nfe/ws/consultaNFeEmitidas",
    "ConsultaNFeRecebidas": "http://www.prefeitura.sp.gov.br/nfe/ws/consultaNFeRecebidas",
    "EnvioLoteRPS": "http://www.prefeitura.sp.gov.br/nfe/ws/envioLoteRPS",
    "EnvioRPS": "http://www.prefeitura.sp.gov.br/nfe/ws/envioRPS",
    "TesteEnvioLoteRPS": "http://www.prefeitura.sp.gov.br/nfe/ws/testeenvio",
    #Async
    "ConsultaGuiaSync": "http://www.prefeitura.sp.gov.br/nfe/ws/consultaGuia",
    "ConsultaSituacaoGuiaSync": "http://www.prefeitura.sp.gov.br/nfe/ws/consultaSituacaoGuia",
    "ConsultaSituacaoLoteSync": "http://www.prefeitura.sp.gov.br/nfe/ws/consultaSituacaoLote",
    "EmissaoGuiaAsync": "http://www.prefeitura.sp.gov.br/nfe/ws/emissaoGuia",
    "EnvioLoteRpsAsync": "http://www.prefeitura.sp.gov.br/nfe/ws/envioLoteRPSAsync",
    "TesteEnvioLoteRpsAsync": "http://www.prefeitura.sp.gov.br/nfe/ws/testeEnvioLoteRPSAsync",
}

method2tag = {
    "TesteEnvioLoteRpsAsync": "TesteEnvioLoteRPS",
    "EnvioLoteRpsAsync": "EnvioLoteRPS",
    "ConsultaSituacaoLoteSync": "ConsultaSituacaoLote",
    "CancelamentoNFe": "CancelamentoNFe",
}

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=True
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    referencia = ""
    if method in ["EnvioLoteRPS","EnvioLoteRpsAsync"]:
        kwargs["nfse"]["total_servicos"] = sum(Decimal(rps["servico"]["valor_servico"]) for rps in kwargs["nfse"]["lista_rps"] if "valor_servico" in rps["servico"]) or Decimal("0.00")
        kwargs["nfse"]["total_deducoes"] = sum(Decimal(rps["servico"]["deducoes"]) for rps in kwargs["nfse"]["lista_rps"] if "deducoes" in rps["servico"]) or Decimal("0.00")

        for i, rps in enumerate(kwargs['nfse']['lista_rps']):
            kwargs['nfse']['lista_rps'][i]['status'] = "N" if rps['status'] == "1" else "C"
            kwargs['nfse']['lista_rps'][i]['servico']['iss_retido'] = "S" if rps['servico']['iss_retido'] == "1" else "N"


    xml_string_send = render_xml(path, "%s.xml" % method, True, False, **kwargs)
    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    if method in ["EnvioLoteRPS","EnvioLoteRpsAsync"]:
        #Assina os RPS
        signer.gerar_assinatura_rps(xml_send,**kwargs)
        #Assina o lote
        xml_signed_send = signer.assina_xml(xml_send)
    elif method == "CancelamentoNFe":
        #Assina o cancelamento
        signer.gerar_assinatura_cancelamento(xml_send,**kwargs)
        xml_signed_send = etree.tostring(xml_send)
    else:
        xml_signed_send = etree.tostring(xml_send)

    #xml_signed_send = re.sub(r'[\r\n]','',xml_signed_send)
    print ('--- xml ---')
    print (xml_signed_send)

    return xml_signed_send

def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")

    url = kwargs.get("base_url",None)

    if method in "EnvioLoteRPS" and kwargs.get("ambiente", "producao") == "homologacao":
        method = "TesteEnvioLoteRPS"
    elif method in "EnvioLoteRpsAsync" and kwargs.get("ambiente", "producao") == "homologacao":
        method = "TesteEnvioLoteRpsAsync"

    xml_send = kwargs["xml"]
    if not url and method in [
        "ConsultaGuiaSync","ConsultaSituacaoGuiaSync",
        "ConsultaSituacaoLoteSync","EmissaoGuiaAsync",
        "EnvioLoteRpsAsync","TesteEnvioLoteRpsAsync"]:
        url = "https://nfews.prefeitura.sp.gov.br/lotenfeasync.asmx"
    else:
        url = "https://nfe.prefeitura.sp.gov.br/ws/lotenfe.asmx"

    path = os.path.join(os.path.dirname(__file__), "templates")
    tag = method2tag[method] if method in method2tag else method
    soap = render_xml(path, "SoapRequest.xml", False, False, **{"soap_body":xml_send, "method": tag })
    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": op2action[method],
        "Operation": method,
        "Content-length": str(len(soap))
    }
    request = session.post(url, data=soap, headers=headers)
    response, obj = sanitize_response(request.content.decode('utf8', 'ignore'))
    try:
        return {"sent_xml": str(soap), "received_xml": str(response.encode('utf8')), "object": obj.Body }
    except:
        return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "EnvioLoteRpsAsync", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "EnvioLoteRpsAsync", **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelamentoNFe", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    response = _send(certificado, "CancelamentoNFe", **kwargs)
    xml = None

    try:
         #Conversão a objeto e Busca pelo elemento Nfse
        res, xml_obj = sanitize_response(response['object']['ConsultaSituacaoLoteResponse']['RetornoXML']['ResultadoOperacao'].text)
        #Caso haja algum erro, as mensagens serão retornadas
        if xml_obj.findall(".//Alerta"):
            xml = ""
            for xmlobj in xml_obj.findall(".//Alerta"):
                xml += etree.tostring(xmlobj)
        else:
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
    return _render(certificado, "ConsultaSituacaoLoteSync", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultaSituacaoLoteSync", **kwargs)
    xml = None

    try:
        #Conversão a objeto e Busca pelo elemento Nfse
        res, xml_obj = sanitize_response(response['object']['ConsultaSituacaoLoteResponse']['RetornoXML']['ResultadoOperacao'].text)
        #Caso haja algum erro, as mensagens serão retornadas
        if xml_obj.findall(".//Alerta"):
            xml = ""
            for xmlobj in xml_obj.findall(".//Alerta"):
                xml += etree.tostring(xmlobj)
        else:
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
        print(err)
        pass

    return xml
