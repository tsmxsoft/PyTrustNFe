# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.dsf.assinatura import Assinatura
from pytrustnfe.utils import ibge2siafi
from lxml import etree
from zeep.transports import Transport
from requests import Session
import requests
from datetime import datetime, timedelta
from decimal import Decimal


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)
    
    #Buscar o código do SIAFI pelo ibge ou pelo cnpj da prefeitura
    cnpj_pref = kwargs["nfse"].get("cnpj_prefeitura", None)
    if method == "enviar":
        ibge_cid = kwargs["nfse"]["lista_rps"][0]["servico"].get("codigo_municipio", None)
        kwargs["nfse"]["total_servicos"] = "{0:.2f}".format(sum(Decimal(rps["servico"]["valor_servico"]) for rps in kwargs["nfse"]["lista_rps"]))
        kwargs["nfse"]["total_deducoes"] = "{0:.2f}".format(sum(Decimal(rps["servico"]["deducoes"]) for rps in kwargs["nfse"]["lista_rps"] if "deducoes" in rps["servico"]))
    else:
        ibge_cid = kwargs["nfse"]["codigo_municipio"]
    kwargs["nfse"]["cidade"] = ibge2siafi(ibge_cid) if ibge_cid else ibge2siafi(cnpj_pref)

    if method == "enviar":
        #Processar campos dos RPS
        for i, rps in enumerate(kwargs["nfse"]["lista_rps"]):
            #==========
            #Operação
            #==========
            operacao = None
            #“C” - Imune/Isenta de ISSQN
            if str(rps["eligibilidade_iss"]) in ['3','5']:
                operacao = "C"
            #“B”- Com Dedução/Materiais
            elif "deducoes" in rps["servico"] and not rps["servico"]["deducoes"] == "0.00":
                operacao = "B"
            #“J” – Intermediação
            elif "intermediario" in rps:
                operacao = "J"
            #“A”- Sem Dedução
            else:
                operacao = "A"

            kwargs["nfse"]["lista_rps"][i]["operacao"] = operacao
            
            #==========
            #Tributação
            #==========
            tributacao = None
            #M – Micro Empreendedor Individual (MEI)
            if str(rps["regime_tributacao"]) == "5":
                tributacao = "M"
            #C - Isenta de ISS
            elif str(rps["natureza_operacao"]) == '3':
                tributacao = "C"
            #F - Imune
            elif str(rps["natureza_operacao"]) == '4':
                tributacao = "F"
            #K – Exigibilidade Sus.Dec. J/Proc.A
            elif str(rps["natureza_operacao"]) in ['5','6']:
                tributacao = "K"
            #H - Tributável - Simples Nacional
            elif str(rps["optante_simples"]) == "1":
                tributacao = "H"
            #E - Não Incidência no Município
            elif str(rps["natureza_operacao"]) in ['1','2'] and str(rps["servico"]["codigo_municipio"]) != str(rps["tomador"]["codigo_municipio"]):
                tributacao = "E"
            #N - Não tributável
            elif str(rps["natureza_operacao"]) in ['1','2'] and str(rps["servico"]["iss"]) == "0.00":
                tributacao = "N"
            #T - Tributável
            elif str(rps["natureza_operacao"]) in ['1','2'] and Decimal(rps["servico"]["iss"]) > Decimal("0.00"):
                tributacao = "T"
            else:
                #G - Tributável Fixo
                tributacao = "G"
            
            kwargs["nfse"]["lista_rps"][i]["tributacao"] = tributacao
            
            #==========
            #Itens (por padrão vai apenas 1)
            #==========
            kwargs["nfse"]["lista_rps"][i]["itens"] = [
                {
                    "descricao": rps["servico"]["discriminacao"],
                    "quantidade": 1,
                    "valor_unitario": rps["servico"]["valor_servico"],
                    "valor_total": rps["servico"]["valor_servico"],
                }]
        signer.gerar_assinatura_rps(**kwargs)

    xml_string_send = render_xml(path, "%s.xml" % method, True, False, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    if method in ["enviar","consultarNFSeRps","cancelar"]:
        xml_signed_string = signer.assina_xml(xml_send, "lote:%s" % (kwargs["nfse"].get("numero_lote", None) or "1"))
    else:
        xml_signed_string = etree.tostring(xml_send)

    return xml_signed_string

def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")

    url = kwargs["base_url"]

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
        "SOAPAction": "",
        "Operation": method,
        "Content-length": str(len(soap))
    }

    request = requests.post(url, data=soap, headers=headers)
    print(request.content)
    response, obj = sanitize_response(request.content.decode('utf8', 'ignore'))
    return {"sent_xml": str(soap), "received_xml": str(response.encode('utf8')), "object": obj.Body }

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "enviar", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "enviar", **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "cancelar", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "cancelar", **kwargs)

def xml_consulta_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "consultarNFSeRps", **kwargs)

def consulta_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consulta_nfse_por_rps(certificado, **kwargs)
    return _send(certificado, "consultarNFSeRps", **kwargs)

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "consultarLote", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, "consultarLote", **kwargs)

def xml_consultar_nota(certificado, **kwargs):
    return _render(certificado, "consultarNota", **kwargs)

def consultar_nota(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nota(certificado, **kwargs)
    return _send(certificado, "consultarNota", **kwargs)

