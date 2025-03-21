# -*- coding: utf-8 -*-
import requests
from datetime import datetime
import json as jsonlib
import jwt
import requests
######################################################

def get_ecode(nfse):
    token = nfse['chave_digital']

    try:
        ecode = jwt.decode(token, verify=False)['primarysid']
    except:
        raise Exception('eCode não encontrado na chave digital')
    return ecode
    

######################################################

# Até então, não disponibilizado pelo WebService
def consultar_lote_rps(**kwargs):
  pass


def recepcionar_lote_rps(certificado = None, **kwargs):
    base_url = kwargs.get('base_url')
    nfse = kwargs.get('nfse')
    token = nfse['chave_digital']
    ecode = get_ecode(nfse)

    if kwargs['base_url']:
        base_url = base_url
    else:
        base_url = 'https://enfseapi.elmartecnologia.com.br'

    prestadorCpfCnpj = nfse['cnpj_prestador']

    
    
    headers = {}
    headers['Authorization'] = 'Bearer %s' % token
    json = {}
    json['rps'] = _obj_send_parser(**kwargs)

    
    
    urlRps = base_url + '/%s/api/Rps/%s' % (ecode, prestadorCpfCnpj)

    response = requests.post(urlRps, headers=headers, json=json)


    if response.status_code == 200 and response.json():
        return {"sent_xml": jsonlib.dumps(json), "received_xml": jsonlib.dumps(response.json()), "object": response.json()}
    
    return {"sent_xml": jsonlib.dumps(json), "received_xml": str(response.content), "object": None }
    

    
    


def _obj_send_parser(**kwargs):
    nfse = kwargs.get('nfse')
    rpsList = []

    for rps in nfse['lista_rps']:
        rps_dict = {
            "rps": {
                "identificacaoRps": {
                    "numero": rps["numero"],
                    "serie": rps["serie"],
                    "tipo": rps["tipo_rps"]
                },
                "dataEmissao": rps["data_emissao"],
                "dataEmissaoRps": rps["data_emissao"],
                "status": rps["status"]
            },
            "naturezaOperacao": rps["natureza_operacao"],
            "optanteSimplesNacional": rps["optante_simples"],
            "incentivadorCultural": rps["incentivador_cultural"],
            "competencia": rps["data_competencia"],
            "servico": {
                "valores": {
                    "valorServicos": float(rps["servico"]["valor_servico"]),
                    "valorDeducoes": rps["servico"].get("deducoes", 0.00),
                    "valorDescontoIncondicionado": rps["servico"].get("desconto_incondicionado", 0.00),
                    "valorDescontoCondicionado": rps["servico"].get("desconto_condicionado", 0.00),
                    "valorPis": rps["servico"].get("pis", 0.00),
                    "valorInss": rps["servico"].get("inss", 0.00),
                    "valorIr": rps["servico"].get("ir", 0.00),
                    "valorCsll": rps["servico"].get("csll", 0.00),
                    "valorIssRetido": float(rps["servico"]["iss_retido"]) if int(rps["servico"]["iss_retido"]) == 2 else 0.00,
                    "valorIss": float(rps["servico"]["iss"]),
                    "outrasRetencoes": rps["servico"].get("outras_retencoes", 0.00),
                    "baseCalculo": float(rps["servico"]["base_calculo"]),
                    "aliquota": float(rps["servico"]["aliquota"]) * 100.00,
                    "valorLiquidoNfse": float(rps["servico"]["valor_liquido_nfse"]),
                    "valorCofins": rps["servico"].get("cofins", 0.00),
                    "descontoIncondicionado": rps["servico"].get("desconto_incondicionado", 0.00),
                    "descontoCondicionado": rps["servico"].get("desconto_condicionado", 0.00)
                },
                "itemListaServico": rps["servico"]["codigo_servico"],
                "codigoCnae": rps["servico"]["cnae_servico"],
                "ativEconomica": rps["servico"]["cnae_servico"],
                "discriminacao": rps["servico"]["discriminacao"] or "",
                "codigoMunicipio": rps["servico"]["codigo_municipio"],
                "codigoTributacaoMunicipio": rps["codigo_tributacao_municipio"],
                "regimeEspecialTributacao": rps["regime_tributacao"],
                "municipioIncidencia": rps["servico"]["codigo_municipio"],
                "exigibilidadeISS": rps["eligibilidade_iss"]
            },
            "valorCredito": rps.get("valor_credito", 0.00),
            "tomador": {
                "razaoSocial": rps["tomador"]["razao_social"],
                "identificacaoTomador": {
                    "cpfCnpj": {
                        "cpf": rps["tomador"]["cpf_cnpj"] if len(rps["tomador"]["cpf_cnpj"].strip()) == 11 else "",
                        "cnpj": rps["tomador"]["cpf_cnpj"] if len(rps["tomador"]["cpf_cnpj"].strip()) != 11 else ""
                    },
                    "inscricaoMunicipal": rps["tomador"].get("inscricao_municipal", ""),
                    "razaoSocial": rps["tomador"]["razao_social"]
                },
                "endereco": {
                    "logradouro": rps["tomador"]["endereco"],
                    "numero": rps["tomador"]["numero"],
                    "bairro": rps["tomador"]["bairro"],
                    "codigoMunicipio": rps["tomador"]["codigo_municipio"],
                    "uf": rps["tomador"]["uf"],
                    "cep": rps["tomador"]["cep"],
                    "complemento": ""
                },
                "contato": {
                    "telefone": rps["tomador"]["telefone"],
                    "email": rps["tomador"]["email"]
                }
            }
        }
        
        rpsList.append(rps_dict)

    return rpsList

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _obj_send_parser(**kwargs)




