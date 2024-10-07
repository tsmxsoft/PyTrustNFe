# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

#Homologação: https://www.producaorestrita.nfse.gov.br/swagger/contribuintesissqn/#/
#Produção: https://www.nfse.gov.br/swagger/contribuintesissqn/#/

import os
import sys
import certifi
import requests
from copy import copy
from lxml import etree
from decimal import Decimal
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.utils import gerar_chave_nfsenacional, gerar_chave_nfsenacional_dps, gerar_chave_nfsenacional_pedido_registro, \
    ChaveNFSeNacional, ChaveNFSeNacionalDPS, ChaveNFSeNacionalEvento, ChaveNFSeNacionalPedidoRegistro
from pytrustnfe.Servidores import localizar_url
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfsenacional.assinatura import Assinatura
#B64 + Gzip
import gzip
import base64
try:
    from StringIO import StringIO
except ImportError:
    import io as StringIO

VERSAO = "1.00"

def _generate_nfse_id(**kwargs):
    vals = {
        "ibge_mun": kwargs["NFSe"]["infNFSe"]["cLocEmi"],
        "ambiente": kwargs["NFSe"]["infNFSe"]["ambGer"],
        "tipo_insc_fed": 1 if len(kwargs["NFSe"]["infNFSe"]["emit"]["cnpj_cpf"]) == 11 else 2,
        "insc_fed": kwargs["NFSe"]["infNFSe"]["emit"]["cnpj_cpf"],
        "numero": kwargs["NFSe"]["infNFSe"]["nNFSe"],
        "dt_emissao": "%s%s"
        % (
            kwargs["NFSe"]["infNFSe"]["DPS"]["infDPS"]["dhEmi"][2:4],
            kwargs["NFSe"]["infNFSe"]["DPS"]["infDPS"]["dhEmi"][5:7],
        ),
        "codigo": kwargs["NFSe"]["infNFSe"]["cNFSe"],
    }
    chave_nfse = ChaveNFSeNacional(**vals)
    chave_nfse = gerar_chave_nfsenacional(chave_nfse, "NFS")
    kwargs["NFSe"]["infNFSe"]["Id"] = chave_nfse


def _generate_nfse_dps_id(**kwargs):
    dps = kwargs["DPS"]["infDPS"]
    vals = {
        "ibge_mun": dps["cLocEmi"],
        "tipo_insc_fed": 1 if len(dps["prest"]["cnpj_cpf"]) == 11 else 2,
        "insc_fed": dps["prest"]["cnpj_cpf"],
        "serie": dps["serie"],
        "numero": dps["nDPS"],
    }
    chave_nfse_dps = ChaveNFSeNacionalDPS(**vals)
    chave_nfse_dps = gerar_chave_nfsenacional_dps(chave_nfse_dps, "DPS")
    kwargs["DPS"]["Id"] = chave_nfse_dps


def _generate_evento_id(**kwargs):
    evento = kwargs["Evento"]["infEvento"]
    vals = {
        "id_pedido": evento["pedRegEvento"]["infPedReg"]["Id"],
        "nseq_evento": evento["nSeqEvento"],
    }
    chave_nfse_evento = ChaveNFSeNacionalEvento(**vals)
    chave_nfse_evento = gerar_chave_nfsenacional_dps(chave_nfse_evento, "EVT")
    kwargs["DPS"]["Id"] = chave_nfse_evento


def _generate_evento_pedreg_id(**kwargs):
    evento = kwargs["pedRegEvento"]
    cod_evento = ""
    for x in evento["infPedReg"].keys():
        if x.startswith("e") and len(x) == 7:
            cod_evento = x[1:]
    vals = {
        "chave_acesso": evento["infPedReg"]["chNFSe"],
        "cod_evento": cod_evento,
        "nPedRegEvento": evento["infPedReg"]["nPedRegEvento"],
    }
    chave_nfse_pedreg = ChaveNFSeNacionalPedidoRegistro(**vals)
    chave_nfse_pedreg = gerar_chave_nfsenacional_pedido_registro(chave_nfse_pedreg, "PRE")
    kwargs["pedRegEvento"]["Id"] = chave_nfse_pedreg


def _render(certificado, method, sign, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)
    xml_string_send = render_xml(path, "%s_%s.xml" % (method, VERSAO), True, **kwargs)
    
    xmlElem_send = etree.fromstring(
        xml_string_send, parser=parser)

    if sign:
        signer = Assinatura(certificado.pfx, certificado.password)
        if method == "DPS":
            #Assina DPS
            xml_send = signer.assina_xml(xmlElem_send, kwargs["DPS"]["Id"])
        elif method == "pedRegEvento":
            #Assina pedido de registro de evento
            xml_send = signer.assina_xml(xmlElem_send, kwargs["pedRegEvento"]["Id"])
    else:
        if sys.version_info[0] > 2:
            xml_send = etree.tostring(xmlElem_send, encoding=str)
        else:
            xml_send = etree.tostring(xmlElem_send, encoding="utf8")

    if kwargs.get("b64encode"):
        out_file = StringIO()
        gzip_file = gzip.GzipFile(fileobj=out_file, mode='wb')
        gzip_file.write(xml_send.encode('utf-8'))
        gzip_file.close()
        b64_bytes = base64.b64encode(out_file.getvalue())
        xml_send = b64_bytes.decode('utf-8')

    return xml_send


def _send(certificado, method, **kwargs):
    kwargs["base_url"] = "https://sefin.nfse.gov.br/sefinnacional"
    if "ambiente" in kwargs:
        if kwargs["ambiente"] == "homologacao":
            kwargs["base_url"] = "https://sefin.producaorestrita.nfse.gov.br/SefinNacional"
        
    base_url = kwargs["base_url"] if "base_url_append" not in kwargs else kwargs["base_url"] + kwargs["base_url_append"]
    xml_send = kwargs.get("xml",None)
    method_request = kwargs.get("method_request", "GET")
    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    headers = {
        "Content-Type": "application/json",
    }
    params = {}
    payload = {}
    if method == "DPS":
        payload = {
            "dpsXmlGZipB64": xml_send,
        }
    elif method == "pedRegEvento":
        payload = {
            "pedidoRegistroEventoXmlGZipB64": xml_send,
        }
    request = requests.request(method_request, base_url,json=payload, params=params, cert=(cert, key), headers=headers, verify=certifi.where())
    return {"sent_xml": xml_send, "received": request.text, "obj": request}


def xml_autorizar_dps(certificado, **kwargs):
    _generate_nfse_dps_id(**kwargs)
    return _render(certificado, "DPS", True, **kwargs)


def autorizar_dps(certificado, **kwargs):
    """
    Ao retornar com sucesso o objeto retornado é:
    {
        "versaoAplicativo": string
        "idDps": string 
        "alertas": arary object or null
        "chaveAcesso": string
        "tipoAmbiente": 1 - Produção, 2 - Homologação,
        "dataHoraProcessamento: datetime with timezone,
        "nfseXmlGZipB64": string (xml da nfse comprimido e codificado base64)
    }
    """
    kwargs["b64encode"] = True
    if "xml" not in kwargs:
        kwargs["xml"] = xml_autorizar_dps(certificado, **kwargs)
    kwargs["base_url_append"] = "/nfse/"
    kwargs["method_request"] = "POST"
    return _send(certificado, "DPS", **kwargs)

def xml_registrar_evento(certificado, **kwargs):
    _generate_evento_pedreg_id(**kwargs)
    return _render(certificado, "pedRegEvento", True, **kwargs)

def registrar_evento(certificado, **kwargs):
    assert "pedRegEvento" in kwargs, "Necessário informar o objeto pedRegEvento"
    assert "infPedReg" in kwargs["pedRegEvento"], "Necessário informar os dados do evento"
    assert "chNFSe" in kwargs["pedRegEvento"]["infPedReg"], "Necessário informar o campo chNFSe contendo chave da NFSe"
    
    kwargs["b64encode"] = True
    if "xml" not in kwargs:
        kwargs["xml"] = xml_registrar_evento(certificado, **kwargs)
    kwargs["base_url_append"] = "/nfse/%s/eventos/" % (kwargs["pedRegEvento"]["infPedReg"]["chNFSe"])
    kwargs["method_request"] = "POST"
    return _send(certificado, "pedRegEvento", **kwargs)

def retorna_nfse(certificado, **kwargs):
    """
    Ao retornar com sucesso o objeto retornado é:
    {
        "versaoAplicativo": string
        "chaveAcesso": string
        "tipoAmbiente": 1 - Produção, 2 - Homologação,
        "dataHoraProcessamento: datetime with timezone,
        "nfseXmlGZipB64": string (xml da nfse comprimido e codificado base64) 
    }
    """
    assert "chaveAcesso" in kwargs, "Necessário informar parâmetro chaveAcesso"
    
    kwargs["base_url_append"] = "/nfse/" + str(kwargs["chaveAcesso"])
    return _send(certificado, "", **kwargs)


def verificar_dps(certificado, **kwargs):
    """
    Ao retornar com sucesso o objeto retornado é:
    {
        "versaoAplicativo": string
        "chaveAcesso": string
        "tipoAmbiente": 1 - Produção, 2 - Homologação,
        "dataHoraProcessamento: datetime with timezone,
    }
    """
    assert "DPS" in kwargs, "Necessário informar parâmetro DPS"
    
    kwargs["base_url_append"] = "/dps/" + kwargs["DPS"]["Id"]
    kwargs["method_request"] = "GET"
    return _send(certificado, "", **kwargs)


def retorna_municipio_aliquota(certificado, **kwargs):
    """
    Campos requisitados:
    codigoMunicipio ($int32) - O código do município deve ser composto por sete dígitos.
    codigoServico (string) - O código do serviço deve ser informado no formato 00.00.00.000.
    competencia ($date-time) - No formato MM/DD/YYYY
    
    Retorno (200):
    {
        "dataHoraProcessamento": "2024-04-24T13:32:44.338Z",
        "tipoAmbiente": 1,
        "aliquotas": {
            "additionalProp1": [
            {
                "aliq": 0,
                "dtIni": "2024-04-24T13:32:44.338Z",
                "dtFim": "2024-04-24T13:32:44.338Z"
            }
            ],
            "additionalProp2": [
            {
                "aliq": 0,
                "dtIni": "2024-04-24T13:32:44.338Z",
                "dtFim": "2024-04-24T13:32:44.338Z"
            }
            ],
            "additionalProp3": [
            {
                "aliq": 0,
                "dtIni": "2024-04-24T13:32:44.338Z",
                "dtFim": "2024-04-24T13:32:44.338Z"
            }
            ]
        },
        "mensagem": "string"
    }

    """
    assert "codigoMunicipio" in kwargs, "Necessário informar parâmetro codigoMunicipio"
    assert "codigoServico" in kwargs, "Necessário informar parâmetro codigoServico"
    assert "competencia" in kwargs, "Necessário informar parâmetro competencia"
    
    kwargs["base_url_append"] = "/parametros_municipais/%s/%s/%s/aliquota" % (
        kwargs["codigoMunicipio"],
        kwargs["codigoServico"],
        kwargs["competencia"],
    )
    return _send(certificado, "", **kwargs)


def retorna_municipio_convenios(certificado, **kwargs):
    """
    Campos requisitados:
    codigoMunicipio ($int32) - O código do município deve ser composto por sete dígitos.
    
    Retorno (200):
    {
        "dataHoraProcessamento": "2024-04-24T13:33:43.840Z",
        "tipoAmbiente": 1,
        "parametrosConvenio": {
            "tipo": 1,
            "aderenteAmbienteNacional": 0,
            "aderenteEmissorNacional": 0,
            "aderenteMAN": 0,
            "permiteAproveitametoDeCreditos": true
        },
        "mensagem": "string"
    }
    """
    assert "codigoMunicipio" in kwargs, "Necessário informar parâmetro codigoMunicipio"
    
    kwargs["base_url_append"] = "/parametros_municipais/%s/convenio" % (
        kwargs["codigoMunicipio"],
    )
    return _send(certificado, "", **kwargs)


def retorna_municipio_regimes_especiais(certificado, **kwargs):
    """
    Campos requisitados:
    codigoMunicipio ($int32) - O código do município deve ser composto por sete dígitos.
    codigoServico (string) - O código do serviço deve ser informado no formato 00.00.00.000.
    competencia ($date-time) - No formato MM/DD/YYYY
    
    Retorno (200):
    {
        "dataHoraProcessamento": "2024-04-24T13:35:11.279Z",
        "tipoAmbiente": 1,
        "regimesEspeciais": {
            "additionalProp1": {
            "additionalProp1": [
                {
                "sit": 1,
                "dtIni": "2024-04-24T13:35:11.279Z",
                "dtFim": "2024-04-24T13:35:11.279Z",
                "motivo": "string"
                }
            ],
            "additionalProp2": [
                {
                "sit": 1,
                "dtIni": "2024-04-24T13:35:11.279Z",
                "dtFim": "2024-04-24T13:35:11.279Z",
                "motivo": "string"
                }
            ],
            "additionalProp3": [
                {
                "sit": 1,
                "dtIni": "2024-04-24T13:35:11.279Z",
                "dtFim": "2024-04-24T13:35:11.279Z",
                "motivo": "string"
                }
            ]
            },
            "additionalProp2": {
            "additionalProp1": [
                {
                "sit": 1,
                "dtIni": "2024-04-24T13:35:11.279Z",
                "dtFim": "2024-04-24T13:35:11.279Z",
                "motivo": "string"
                }
            ],
            "additionalProp2": [
                {
                "sit": 1,
                "dtIni": "2024-04-24T13:35:11.279Z",
                "dtFim": "2024-04-24T13:35:11.279Z",
                "motivo": "string"
                }
            ],
            "additionalProp3": [
                {
                "sit": 1,
                "dtIni": "2024-04-24T13:35:11.279Z",
                "dtFim": "2024-04-24T13:35:11.279Z",
                "motivo": "string"
                }
            ]
            },
            "additionalProp3": {
            "additionalProp1": [
                {
                "sit": 1,
                "dtIni": "2024-04-24T13:35:11.279Z",
                "dtFim": "2024-04-24T13:35:11.279Z",
                "motivo": "string"
                }
            ],
            "additionalProp2": [
                {
                "sit": 1,
                "dtIni": "2024-04-24T13:35:11.279Z",
                "dtFim": "2024-04-24T13:35:11.279Z",
                "motivo": "string"
                }
            ],
            "additionalProp3": [
                {
                "sit": 1,
                "dtIni": "2024-04-24T13:35:11.279Z",
                "dtFim": "2024-04-24T13:35:11.279Z",
                "motivo": "string"
                }
            ]
            }
        },
        "mensagem": "string"
    }
    """
    assert "codigoMunicipio" in kwargs, "Necessário informar parâmetro codigoMunicipio"
    assert "codigoServico" in kwargs, "Necessário informar parâmetro codigoServico"
    assert "competencia" in kwargs, "Necessário informar parâmetro competencia"
    
    kwargs["base_url_append"] = "/parametros_municipais/%s/%s/%s/regimes_especiais" % (
        kwargs["codigoMunicipio"],
        kwargs["codigoServico"],
        kwargs["competencia"],
    )
    return _send(certificado, "", **kwargs)

#========================================
#Adaptadores Abrasf > NFSe Nacional
#========================================


def _abrasf_adapter(**kwargs):
    nfse_abrasf = kwargs["rps"]
    ambiente = kwargs["ambiente"]
    #optante do simples
    op_simples = None
    if str(nfse_abrasf["optante_simples"]) == '1' and str(nfse_abrasf["regime_tributacao"]) == '5':
        op_simples = '2'
    elif str(nfse_abrasf["optante_simples"]) == '1' and str(nfse_abrasf["regime_tributacao"]) == '6':
        op_simples = '3'
    else:
        op_simples = '1'
    #regime especial de tributação
    reg_esp_trib = None
    if str(nfse_abrasf["regime_tributacao"]) == '4':
        reg_esp_trib = '1'
    elif str(nfse_abrasf["regime_tributacao"]) == '2':
        reg_esp_trib = '2'
    elif str(nfse_abrasf["regime_tributacao"]) == '1':
        reg_esp_trib = '3'
    elif str(nfse_abrasf["regime_tributacao"]) == '3':
        reg_esp_trib = '6'
    else:
        reg_esp_trib = '0'

    nfse_base = {
        "infDPS": {
            "tpAmb": "1" if ambiente == "producao" else "2",
            "verAplic": "PyTrustNFe3",
            "serie": nfse_abrasf["serie"],
            "tpEmit":  "1",
            "prest": {
                "IM": nfse_abrasf["prestador"].get("inscricao_municipal",""),
                "cnpj_cpf": nfse_abrasf["prestador"]["cnpj"],
                "regTrib": {
                    "opSimplNac": op_simples,
                    "regApTribSN": nfse_abrasf["optante_simples"],
                    "regEspTrib": reg_esp_trib,
                }
            }
        }
    }

    #Exigibilidade ISS
    eligibilidade_iss = None
    if str(nfse_abrasf["natureza_operacao"]) in ['1','2','5','6']:
        eligibilidade_iss = '1'
    elif str(nfse_abrasf["natureza_operacao"]) == '4':
        eligibilidade_iss = '2'
    if "iss" not in nfse_abrasf["servico"] or \
        ("iss" in nfse_abrasf["servico"] and Decimal(nfse_abrasf["servico"]["iss"]) == Decimal('0.00')):
        eligibilidade_iss = '4'
    if str(nfse_abrasf["servico"]["codigo_municipio"]) == '9999999':
        eligibilidade_iss = '3'

    nfse = copy(nfse_base)
    aliquota = Decimal(0.0)
    if "aliquota" in nfse_abrasf["servico"]:
        aliquota = Decimal(nfse_abrasf["servico"]["aliquota"]) * Decimal("100.00")
    nfse["infDPS"].update({
        "dhEmi": str(nfse_abrasf["data_emissao"]) + "-03:00",
        "nDPS": nfse_abrasf["numero"],
        "dCompet": str(nfse_abrasf["data_competencia"]).split("T")[0],
        "cLocEmi": nfse_abrasf["servico"]["codigo_municipio"],
        "toma": {
            "cnpj_cpf": nfse_abrasf["tomador"]["cpf_cnpj"],
            "xNome": nfse_abrasf["tomador"]["razao_social"],
            "end": {
                "endNac": {
                    "cMun": nfse_abrasf["tomador"]["codigo_municipio"],
                    "CEP": nfse_abrasf["tomador"]["cep"],
                },
                "xLgr": nfse_abrasf["tomador"]["endereco"],
                "nro": nfse_abrasf["tomador"]["numero"],
                "xBairro": nfse_abrasf["tomador"]["bairro"],
            },
            "email": nfse_abrasf["tomador"]["email"],
        },
        "serv": {
            "locPrest": {
                "cLocPrestacao": nfse_abrasf["servico"]["codigo_municipio"],
            },
            "cServ": {
                "cTribNac": nfse_abrasf["servico"]["codigo_atividade"],
                "xDescServ": nfse_abrasf["servico"]["discriminacao"],
                "cIntContrib": nfse_abrasf["servico"]["codigo_servico"],
            },
            "infoCompl": {
                "xInfComp": nfse_abrasf["servico"]["informacao_complementar"],
            }
        },
        "valores": {
            "vServPrest": {
                "vServ": nfse_abrasf["servico"]["valor_servico"],
            },
            "trib": {
                "tribMun": {
                    "tribISSQN": eligibilidade_iss,
                },
                "totTrib": {
                    "pTotTribSN": "%.2f" % (aliquota),
                }
            }
        }
    })

    if str(nfse_abrasf["eligibilidade_iss"]) in ['6','7']:
        nfse["valores"]["trib"]["tribMun"]["exigSusp"] = {
            "tpSusp": 1 if str(nfse_abrasf["eligibilidade_iss"]) == '6' else 2,
            "nProcesso": str(nfse_abrasf["servico"]["numero_processo"]),
        }
    return nfse
    
def xml_recepcionar_lote_rps(certificado, **kwargs):
    lote = kwargs["nfse"]
    
    notas = []
    for nota in lote["lista_rps"]:
        kwargs["rps"] = nota
        kwargs["DPS"] = _abrasf_adapter(**kwargs)
        notas.append(xml_autorizar_dps(certificado, **kwargs))
    return notas


def recepcionar_lote_rps(certificado, **kwargs):
    notas_xml = kwargs.get("XML_Notas", xml_recepcionar_lote_rps(certificado, **kwargs))
    ret = []

    for dps in notas_xml:
        kwargs["XML"] = dps
        ret.append(autorizar_dps(certificado, **kwargs))
    return ret