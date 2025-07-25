# -*- coding: utf-8 -*-
import requests
import json
from pytrustnfe.xml.filters import format_datetime_dmy


def _consultar(base_url,consulta,params = None, data = None):
    req = requests.get(base_url + "prefeitura/" + consulta, data=data, params=params, headers={'Content-Type': 'application/json'})
    if req.status_code == 200:
        if len(req.json()) == 1 and "msg" in req.json()[0]:
            raise Exception(req.json()[0]["msg"])
        return req.json()
    return None


def formatar_cnpj(cnpj):
    cnpj = str(cnpj)
    if len(cnpj) == 14:
        return "{}.{}.{}/{}-{}".format(cnpj[:2], cnpj[2:5], cnpj[5:8], cnpj[8:12], cnpj[12:])
    return cnpj

def formatar_cpf(cpf):
    cpf = str(cpf)
    print('cpf', cpf)
    if len(cpf) == 11:
        return "{}.{}.{}-{}".format(cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])
    return cpf

def formatar_cnae(cnae):
    cnae = str(cnae)
    if len(cnae) == 7:
        return "{}.{}-{}-{}".format(cnae[:2], cnae[2:4], cnae[4:5], cnae[5:])
    return cnae

def formatar_cep(cep):
    cep = str(cep)
    if len(cep) == 8:
        return "{}-{}".format(cep[:5], cep[5:])
    return cep

def _obj_send_parser(**kwargs):
    
    if not isinstance(kwargs.get('rps'), dict):
        raise Exception("Objeto invalido")
    
    rps = kwargs.get('rps')

    rpsobj = {
        "token": kwargs.get("chave_digital"),
        "cnpjcpf": formatar_cnpj(rps["prestador"]["cnpj"]),
        "prefeitura": kwargs.get('prefeitura'),
        "tomador_nome": rps["tomador"]["razao_social"],
        "tomador_cnpjcpf": formatar_cpf(rps["tomador"]["cpf_cnpj"]),
        "tomador_inscrmunicipal": rps["tomador"]["inscricao_municipal"],
        "tomador_logradouro": rps["tomador"]["endereco"],
        "tomador_numero": (int(rps["tomador"]["numero"]) 
                            if str(rps["tomador"]["numero"]).isdigit() 
                            else 0),
        "tomador_bairro": rps["tomador"]["bairro"],
        "tomador_cep": formatar_cep(rps["tomador"]["cep"]),
        "tomador_municipio": rps["tomador"]["cidade"],
        "tomador_uf": rps["tomador"]["uf"],
        "tomador_email": rps["tomador"]["email"],
        "discriminacao": rps["servico"]["discriminacao"],
        "valordeducoes": rps["servico"].get("deducoes", 0.00),
        "codservico": formatar_cnae(rps["servico"]["cnae_servico"]),
        "<issretido>": "S" if rps["servico"]["iss_retido"] == "1" else "N",
        "basecalculo": float(rps["servico"]["base_calculo"]),
        "pispasep": rps["servico"].get("pis", 0.00),
        "cofins": rps["servico"].get("cofins", 0.00),
        "valorinss": rps["servico"].get("inss", 0.00),
        "valorirrf": rps["servico"].get("ir", 0.00),
        "contribuicaosocial": rps["servico"].get("csll", 0.00),
        # "observacao": rps["servico"].get("informacao_complementar", "")
    }

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
            "prefeitura": lote['cnpj_prefeitura'],
            "chave_digital": lote['chave_digital']
            
        })))
    
    return "\n\n".join(ret)


def gerar_nfse(certificado = None, **kwargs):
    obj = [_obj_send_parser(**{
        "base_url": kwargs.get("base_url"),
        "rps": kwargs.get("rps"),
        "prefeitura": kwargs.get('prefeitura'),
        "chave_digital": kwargs.get('chave_digital')
    })]

    form_data = {key: value for o in obj for key, value in o.items()}


    req = requests.post(kwargs.get('base_url'), data=form_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if req.status_code == 200:
        if req.json() and "message" in req.json():
            return {"sent_xml": json.dumps(obj), "received_xml": req.json()["message"], "object": None }
        return {"sent_xml": json.dumps(obj), "received_xml": json.dumps(req.json()), "object": req.json() }
    return {"sent_xml": json.dumps(obj), "received_xml": str(req.content), "object": None }
