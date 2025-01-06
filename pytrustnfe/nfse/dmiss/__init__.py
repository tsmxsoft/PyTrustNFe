# -*- coding: utf-8 -*-
import requests
from datetime import datetime

######################################################

def token(base_url, credenciais):
    url = base_url + '/auth/token'
    response = requests.post(url, json=credenciais)
    if response.status_code == 200:
        return response.json().get('accessToken')
    
    raise Exception(response.text.encode('utf-8') or "Erro ao gerar token")
    
def listarAirps(base_url, **kwargs):
    url = base_url + "/rps/listarAiRps"
    nfse = kwargs.get('nfse')
    accessKeyId = nfse['cnpj_prestador']
    listaAiRps = []

    credenciais = {
        "accessKeyId": accessKeyId,
        "secretAccessKey": accessKeyId[:5]
    }

    headers = {}
    headers['accessToken'] = token(base_url, credenciais)

    json = {}
    json['inscricaoMunicipalPrestador'] = nfse['inscricao_municipal']

    response = requests.post(url, headers=headers, json=json)

    if response.status_code == 200:
        autorizacoesRps = response.json().get('autorizacoesRps')
        for autorizacao in autorizacoesRps:
            listaAiRps.append({"numeroSolicitacao": autorizacao.get('numeroSolicitacao'),
                               "dataSolicitacao": autorizacao.get('dataSolicitacao')})
        return listaAiRps
    
    raise Exception(response.text.encode('utf-8') or "Erro ao listar AiRps") 
    
def solicitarAiRps(base_url, **kwargs):
    url = base_url + "/rps/solicitarAiRps"
    nfse = kwargs.get('nfse')
    accessKeyId = nfse['cnpj_prestador']

    credenciais = {
        "accessKeyId": accessKeyId,
        "secretAccessKey": accessKeyId[:5]
    }

    headers = {}
    headers['accessToken'] = token(base_url, credenciais)

    json = {}
    json['inscricaoMunicipalPrestador'] = nfse['inscricao_municipal']

    response = requests.post(url, headers=headers, json=json)
    if response.status_code == 200:
        return response.json()
    
    raise Exception(response.text.encode('utf-8') or "Erro ao solicitar AiRps")

def consultarAiRps(certificado = None, **kwargs):
    base_url = kwargs.get('base_url')
    nfse = kwargs.get('nfse')
    accessKeyId = nfse['cnpj_prestador']

    credenciais = {
        "accessKeyId": accessKeyId,
        "secretAccessKey": accessKeyId[:5]
    }

    headers = {}
    headers['accessToken'] = token(base_url, credenciais)

    json = {}
    json['inscricaoMunicipalPrestador'] = nfse['inscricao_municipal']
    json['numeroSolicitacao'] = nfse['solicitacao']

    
    url = base_url + "/rps/consultarAiRps"
    response = requests.post(url, headers=headers, json=json)

    if response.status_code == 200:
        return response.json()
    raise Exception(response.text.encode('utf-8') or "Erro ao consultar AiRps")

######################################################

# Até então, não disponibilizado pelo WebService
def consultar_lote_rps(**kwargs):
  pass


def recepcionar_lote_rps(certificado = None, **kwargs):
    base_url = kwargs.get('base_url')
    url = base_url + "/rps/gerarRps"
    nfse = kwargs.get('nfse')

    accessKeyId = nfse['lista_rps'][0]['prestador']['cnpj']
    credenciais = {
        "accessKeyId": accessKeyId,
        "secretAccessKey": accessKeyId[:5]
    }

    headers = {}
    headers['accessToken'] = token(base_url, credenciais)
    
    ambiente = kwargs.get('ambiente')
    if ambiente == "homologacao":
        ambiente = "H"
    else:
        ambiente = "P"

    json = {}
    json['ambiente'] = ambiente
    json['dataSolicitacao'] = datetime.now().strftime('%Y%m%d')
    json['inscricaoMunicipalPrestador'] = nfse['inscricao_municipal']
    json['recibos'] = _obj_send_parser(nfse=nfse)

    response = requests.post(url, headers=headers, json=json)
    
    if response.status_code == 200:
        return response.json()
    
    raise Exception(response.text.encode('utf-8') or "Erro ao recepcionar lote RPS")
    

def _obj_send_parser(**kwargs):
    nfse = kwargs.get('nfse')
    rpsList = []
    
    for rps in nfse['lista_rps']:
        rpsList.append({
        "numero": rps["numero"],
        "codigoVerificacao": rps["codigo_verificacao"],
        "dataHoraEmissao": rps["data_emissao"].replace('-','').replace(':', '').replace('T', ''),
        "situacao": rps["tipo_rps"],
        "naturezaOperacao": rps["status"],
        "valorServicos": float(rps["servico"]["valor_servico"]),
        "valorDeducoes": rps["servico"].get("deducoes", 0.00),
        "descontoCondicionado": rps["servico"].get("desconto_condicionado", 0.00),
        "descontoIncondicionado": rps["servico"].get("desconto_incondicionado", 0.00),
        "baseCalculo": rps["servico"].get("base_calculo", 0.00),
        "aliquota": float(rps["servico"]["aliquota"]),
        "valorIss": float(rps["servico"]["iss"]),
        "issRetidoPeloTomador": "SIM" if int(rps["servico"]["iss_retido"]) == 1 else "NAO",
        "valorPis": rps["servico"].get("pis", 0.00),
        "valorCofins": rps["servico"].get("cofins", 0.00),
        "valorInss": rps["servico"].get("inss", 0.00),
        "valorIrrf": rps["servico"].get("ir", 0.00),
        "valorCsll": rps["servico"].get("csll", 0.00),
        "valorLiquido": float(rps["servico"]["valor_liquido_nfse"]),
        "codigoServico": rps["servico"]["codigo_servico"],
        "codigoCnae": rps["servico"]["cnae_servico"],
        "codigoLocalServico": rps["servico"]["codigo_municipio"],
        "discriminacaoServico": rps["servico"]["discriminacao"] or "",
        "indicadorTomador": "1" if len(rps["tomador"]["cpf_cnpj"].strip()) == 11 else "2",
        "cpfCnpjTomador": rps["tomador"]["cpf_cnpj"],
        "nomeTomador": rps["tomador"]["razao_social"],
        "enderecoTomador": rps["tomador"]["endereco"],
        "bairroTomador": rps["tomador"]["bairro"],
        "cepTomador": rps["tomador"]["cep"],
        "codigoCidadeTomador": rps["tomador"]["codigo_municipio"],
        "emailTomador": rps["tomador"]["email"],
        "numeroEnderecoTomador": rps["tomador"].get("numero", 'SN'),
        "complementoEnderecoTomador": rps["tomador"].get("complemento", ''),
        "inscricaoEstadualTomador": rps["tomador"].get("inscricao_estadual", ''),
        "inscricaoMunicipalTomador": rps["tomador"].get("inscricao_municipal", ''),
        "emailTomador": rps["tomador"].get("email", ''),
        })

    return rpsList

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _obj_send_parser(**kwargs)