# -*- coding: utf-8 -*-
import requests
import json
from pytrustnfe.xml.filters import format_datetime_dmy


def _consultar(base_url, params = None, data = None):
    req = requests.get(base_url, data=data, params=params, headers={'Content-Type': 'application/json'})
    if req.status_code == 200:
        if len(req.json()) == 1 and "msg" in req.json()[0]:
            raise Exception(req.json()[0]["msg"])
        return req.json()
    return None

def token(base_url, credenciais):
    url = base_url + '/auth/token'
    response = requests.post(url, json=credenciais)
    if response.status_code == 200:
        return response.json().get('accessToken')
    else:
        raise Exception("Erro: %s" (response.text))
    
def solicitarAirps(base_url, token, lote):
    url = base_url + "/solicitarAirps"
    headers = {'Authorization': 'Bearer' + token}
    response = requests.post(url, json=lote, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Erro ao solicitar lote de RPS: {response.text}")


def _obj_send_parser(**kwargs):
    if not isinstance(kwargs.get('rps'), dict):
        raise Exception("Objeto invalido")

    base_url = kwargs.get('base_url')
    consulta = kwargs.get('consulta')
    rps = kwargs.get('rps')
    print(base_url, consulta)
    rpsobj = {
        "cnpjPessoaPrestador": rps["prestador"]["cnpj"],
        "razaoSocialPessoaTomador": rps["tomador"]["razao_social"],
        "numeroEnderecoTomador": rps["tomador"].get("numero", 'SN'),
        "complementoEnderecoTomador": rps["tomador"].get("complemento", ''),
        "inscricaoEstadualTomador": rps["tomador"].get("inscricao_estadual", ''),
        "inscricaoMunicipalTomador": rps["tomador"].get("inscricao_municipal", ''),
        "emailTomador": rps["tomador"].get("email", ''),
        "paisLocalPrestacaoServico":    {
            "codigoBacen": 1058,
        },
        "localPrestacaoServico": {
            "codIBGE": rps["tomador"]["codigo_municipio"],
        },
        "servico": {
            "codigo": rps["servico"]["codigo_servico"],
        },
        "aliquota": float(rps["servico"]["aliquota"]) * 100.00,
        "issRetidoPeloTomador": "SIM" if int(rps["servico"]["iss_retido"]) == 1 else "NAO",
        "discriminacaoServico": rps["servico"]["discriminacao"] or '',
        "valorTotal": float(rps["servico"]["valor_servico"]),
        "valorDeducoes": rps["servico"].get("deducoes", 0.00),
        "descontoCondicionado": rps["servico"].get("desconto_condicionado", 0.00),
        "descontoIncondicionado": rps["servico"].get("desconto_incondicionado", 0.00),
        "valorBaseCalculo": rps["servico"].get("base_calculo", 0.00),
        "cofins": rps["servico"].get("cofins", 0.00),
        "csll": rps["servico"].get("csll", 0.00),
        "inss": rps["servico"].get("inss", 0.00),
        "irrf": rps["servico"].get("ir", 0.00),
        "pisPasep": rps["servico"].get("pis", 0.00),
        "rpsDataEmissaoStr": format_datetime_dmy(rps["data_emissao"]),
        "rpsSerie": rps["serie"],
        "rpsNumero": rps["numero"],
        "tokenRPS": kwargs.get('chave_digital'),
    }
    #CPF/CNPJ Tomador
    if len(rps["tomador"]["cpf_cnpj"].strip()) == 11:
        rpsobj["cpfPessoaTomador"] = rps["tomador"]["cpf_cnpj"]
    elif len(rps["tomador"]["cpf_cnpj"].strip()) == 14:
        rpsobj["cnpjPessoaTomador"] = rps["tomador"]["cpf_cnpj"]
    else:
        raise Exception("CPF/CNPJ Tomador Inválido")
    
    #Bairro
    bairroID = None
    if len(rps["tomador"]["bairro"]) == 0:
        raise Exception("Bairro Tomador Inválido")
    ret_bairro = _consultar(kwargs.get('base_url'), 'Bairros', {
        'cmu': rps["tomador"]["codigo_municipio"],
    })
    for bairro in ret_bairro:
        if bairro["nome"].lower().strip() == rps["tomador"]["bairro"].lower().strip():
            bairroID = bairro["id"]
            break
    if bairroID:
        rpsobj["bairroId"] = bairroID
    else:
        rpsobj["bairroEnderecoTomador"] = rps["tomador"]["bairro"]
    
    #Logradouro
    logID = None
    logparams = None
    if len(rps["tomador"]["endereco"]) == 0:
        raise Exception("Logradouro Tomador Inválido")
    if bairroID:
        logparams = {
            'cmu': rps["tomador"]["codigo_municipio"],
            'iba': bairroID,
        }
        retlog = _consultar(kwargs.get('base_url'), 'Logradouros', logparams)
        for log in retlog:
            if log["nome"].lower().strip() == rps["tomador"]["endereco"].lower().strip():
                logID = log["id"]
                break
    if logID:
        rpsobj["logradouroId"] = logID
    else:
        rpsobj["logradouroEnderecoTomador"] = rps["tomador"]["endereco"]

    if bairroID and not logID:
        rpsobj.pop("bairroId")

    return rpsobj

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _obj_send_parser(**kwargs)

def recepcionar_lote_rps(certificado = None, **kwargs):
    lote = kwargs.get('nfse')
    ret = []
    for rps in lote["lista_rps"]:
        ret.append(str(gerar_nfse(**{
            "base_url": kwargs.get("base_url"),
            "rps": rps,
            "chave_digital": lote["chave_digital"],
        })))
    return "\n\n".join(ret)


def gerar_nfse(certificado = None, **kwargs):
    obj = [_obj_send_parser(**{
        "base_url": kwargs.get("base_url"),
        "rps": kwargs.get("rps"),
        "chave_digital": kwargs.get("chave_digital"),
    })]

    req = requests.post(kwargs.get('base_url') + "prefeitura/ws/nfse/emitir", json=obj, headers={'Content-Type': 'application/json'})
    if req.status_code == 200:
        if len(req.json()) == 1 and "msg" in req.json()[0]:
            return {"sent_xml": json.dumps(obj), "received_xml": req.json()[0]["msg"], "object": None }
        return {"sent_xml": json.dumps(obj), "received_xml": json.dumps(req.json()), "object": req.json() }
    return {"sent_xml": json.dumps(obj), "received_xml": str(req.content), "object": None }