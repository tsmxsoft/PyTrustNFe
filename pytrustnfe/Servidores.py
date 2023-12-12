# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# Consultas básicas da NF-e
WS_NFE_INUTILIZACAO = "NfeInutilizacao"
WS_NFE_CONSULTA = "NfeConsultaProtocolo"
WS_NFE_SITUACAO = "NfeStatusServico"
WS_NFE_RECEPCAO_EVENTO = "RecepcaoEvento"
WS_NFE_AUTORIZACAO = "NfeAutorizacao"
WS_NFE_RET_AUTORIZACAO = "NfeRetAutorizacao"

# Alguns estados possuem essa consulta não todos
WS_NFE_CADASTRO = "NfeConsultaCadastro"


# Ambiente nacional
WS_NFCE_QR_CODE = "NfeQRCode"
WS_NFCE_CONSULTA_DESTINADAS = "NfeConsultaDest"
WS_DFE_DISTRIBUICAO = "NFeDistribuicaoDFe"
WS_DOWNLOAD_NFE = "nfeDistDFeInteresse"

# NFCom
WS_NFCOM_CONSULTA = "NFComConsulta"
WS_NFCOM_RECEPCAO = "NFComRecepcao"
WS_NFCOM_RECEPCAO_EVENTO = "NFComRecepcaoEvento"
WS_NFCOM_STATUS_SERVICO = "NFComStatusServico"

#CTe 4.0
WS_CTE400_RECEPCAO_SINC   = "CTeRecepcaoSincV4"
WS_CTE400_RECEPCAO_GTVE   = "CTeRecepcaoGTVeV4"
WS_CTE400_RECEPCAO_OSV    = "CTeRecepcaoOSV4"
WS_CTE400_RECEPCAO_EVENTO = "CTeRecepcaoEventoV4"
WS_CTE400_CONSULTA        = "CTeConsultaV4"
WS_CTE400_STATUS_SERVICO  = "CTeStatusServicoV4"
WS_CTE400_QRCODE          = "QRCode"

# Códigos do ambiente de homologação e produção
AMBIENTE_PRODUCAO = 1
AMBIENTE_HOMOLOGACAO = 2

# Modelos dos documentos eletrônicos
NFE_MODELO   = "55"
NFCE_MODELO  = "65"
NFCOM_MODELO = "62"
CTE_MODELO   = "57"

SIGLA_ESTADO = {
    "12": "AC",
    "27": "AL",
    "13": "AM",
    "16": "AP",
    "29": "BA",
    "23": "CE",
    "53": "DF",
    "32": "ES",
    "52": "GO",
    "21": "MA",
    "31": "MG",
    "50": "MS",
    "51": "MT",
    "15": "PA",
    "25": "PB",
    "26": "PE",
    "22": "PI",
    "41": "PR",
    "33": "RJ",
    "24": "RN",
    "11": "RO",
    "14": "RR",
    "43": "RS",
    "42": "SC",
    "28": "SE",
    "35": "SP",
    "17": "TO",
    "91": "AN",
}


def localizar_url(servico, estado, mod="55", ambiente=2):
    
    # Implementação inicial do NFCom
    # Todos estados utilizam o servidor SVRS
    if mod == NFCOM_MODELO:
        sigla = SIGLA_ESTADO["43"]
    else:
        sigla = SIGLA_ESTADO[estado]
    
    ws = ESTADO_WS[sigla]

    if servico in (WS_DFE_DISTRIBUICAO, WS_DOWNLOAD_NFE):
        ws = AN

    if mod in ws:
        dominio = ws[mod][ambiente]["servidor"]
        complemento = ws[mod][ambiente][servico]
    else:
        dominio = ws[ambiente]["servidor"]
        complemento = ws[ambiente][servico]

    if sigla == "RS" and servico == WS_NFE_CADASTRO:
        dominio = "cad.sefazrs.rs.gov.br"
    if sigla in ("AC", "RN", "PB", "SC", "RJ") and servico == WS_NFE_CADASTRO:
        dominio = "cad.svrs.rs.gov.br"
    if sigla == "AN" and servico == WS_NFE_RECEPCAO_EVENTO:
        dominio = "www.nfe.fazenda.gov.br"
    
    return "https://%s/%s" % (dominio, complemento)


def localizar_qrcode(estado, ambiente=2):
    sigla = SIGLA_ESTADO[estado]
    ws_qrcode = ESTADO_WS[sigla][NFCE_MODELO][ambiente][WS_NFCE_QR_CODE]
    return ws_qrcode


METODO_WS = {
    WS_NFE_AUTORIZACAO: {"webservice": "NfeAutorizacao", "metodo": "NfeAutorizacao",},
    WS_NFE_RET_AUTORIZACAO: {
        "webservice": "NfeRetAutorizacao",
        "metodo": "NfeRetAutorizacao",
    },
    WS_NFE_INUTILIZACAO: {
        "webservice": "NfeInutilizacao2",
        "metodo": "nfeInutilizacaoNF2",
    },
    WS_NFE_CONSULTA: {"webservice": "NfeConsulta2", "metodo": "nfeConsultaNF2",},
    WS_NFE_SITUACAO: {
        "webservice": "NfeStatusServico2",
        "metodo": "nfeStatusServicoNF2",
    },
    WS_NFE_CADASTRO: {
        "webservice": "CadConsultaCadastro2",
        "metodo": "consultaCadastro2",
    },
    WS_NFE_RECEPCAO_EVENTO: {
        "webservice": "RecepcaoEvento",
        "metodo": "nfeRecepcaoEvento",
    },
}

SVRS = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfe.svrs.rs.gov.br",
            WS_NFE_INUTILIZACAO: "ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl",  # noqa
            WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento4.asmx?wsdl",  # noqa
            WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl",  # noqa
            WS_NFE_CADASTRO: "ws/cadconsultacadastro/cadconsultacadastro4.asmx?wsdl",  # noqa
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "nfe-homologacao.svrs.rs.gov.br",
            WS_NFE_INUTILIZACAO: "ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl",  # noqa
            WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento4.asmx?wsdl",  # noqa
            WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl",  # noqa
            WS_NFE_CADASTRO: "ws/cadconsultacadastro/cadconsultacadastro4.asmx?wsdl",  # noqa
        },
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfce.svrs.rs.gov.br",
            WS_NFE_INUTILIZACAO: "ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl",
            WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento4.asmx?wsdl",
            WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl",  # noqa
            WS_NFCE_QR_CODE: "http://dec.fazenda.df.gov.br/ConsultarNFCe.aspx?",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "nfce-homologacao.svrs.rs.gov.br",
            WS_NFE_INUTILIZACAO: "ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl",
            WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento4.asmx?wsdl",
            WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl",  # noqa
            WS_NFCE_QR_CODE: "http://dec.fazenda.df.gov.br/ConsultarNFCe.aspx?",
        },
    },
    NFCOM_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfcom.svrs.rs.gov.br",
            WS_NFCOM_CONSULTA: "WS/NFComConsulta/NFComConsulta.asmx",
            WS_NFCOM_RECEPCAO: "WS/NFComRecepcao/NFComRecepcao.asmx",
            WS_NFCOM_RECEPCAO_EVENTO: "WS/NFComRecepcaoEvento/NFComRecepcaoEvento.asmx",
            WS_NFCOM_STATUS_SERVICO: "WS/NFComStatusServico/NFComStatusServico.asmx",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "nfcom-homologacao.svrs.rs.gov.br",
            WS_NFCOM_CONSULTA: "WS/NFComConsulta/NFComConsulta.asmx",
            WS_NFCOM_RECEPCAO: "WS/NFComRecepcao/NFComRecepcao.asmx",
            WS_NFCOM_RECEPCAO_EVENTO: "WS/NFComRecepcaoEvento/NFComRecepcaoEvento.asmx",
            WS_NFCOM_STATUS_SERVICO: "WS/NFComStatusServico/NFComStatusServico.asmx",
        },
    },
    CTE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "cte.svrs.rs.gov.br",
            WS_CTE400_RECEPCAO_SINC: "ws/CTeRecepcaoSincV4/CTeRecepcaoSincV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "ws/CTeRecepcaoGTVeV4/CTeRecepcaoGTVeV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_OSV: "ws/CTeRecepcaoOSV4/CTeRecepcaoOSV4.asmx?wsdl",
            WS_CTE400_CONSULTA: "ws/CTeConsultaV4/CTeConsultaV4.asmx?wsdl",
            WS_CTE400_STATUS_SERVICO: "ws/CTeStatusServicoV4/CTeStatusServicoV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "ws/CTeRecepcaoEventoV4/CTeRecepcaoEventoV4.asmx?wsdl",
            WS_CTE400_QRCODE: "https://dfe-portal.svrs.rs.gov.br/cte/qrCode",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "cte-homologacao.svrs.rs.gov.br",
            WS_CTE400_RECEPCAO_SINC: "ws/CTeRecepcaoSincV4/CTeRecepcaoSincV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "ws/CTeRecepcaoGTVeV4/CTeRecepcaoGTVeV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_OSV: "ws/CTeRecepcaoOSV4/CTeRecepcaoOSV4.asmx?wsdl",
            WS_CTE400_CONSULTA: "ws/CTeConsultaV4/CTeConsultaV4.asmx?wsdl",
            WS_CTE400_STATUS_SERVICO: "ws/CTeStatusServicoV4/CTeStatusServicoV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "ws/CTeRecepcaoEventoV4/CTeRecepcaoEventoV4.asmx?wsdl",
            WS_CTE400_QRCODE: "https://dfe-portal.svrs.rs.gov.br/cte/qrCode",
        }
    }
}

SVAN = {
    AMBIENTE_PRODUCAO: {
        "servidor": "www.sefazvirtual.fazenda.gov.br",
        WS_NFE_INUTILIZACAO: "NFeInutilizacao4/NFeInutilizacao4.asmx?wsdl",
        WS_NFE_CONSULTA: "NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl",  # noqa
        WS_NFE_SITUACAO: "NFeStatusServico4/NFeStatusServico4.asmx?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl",  # noqa
        WS_NFE_AUTORIZACAO: "NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl",
        WS_NFE_RET_AUTORIZACAO: "NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl",  # noqa
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "hom.sefazvirtual.fazenda.gov.br",
        WS_NFE_INUTILIZACAO: "NFeInutilizacao4/NFeInutilizacao4.asmx?wsdl",
        WS_NFE_CONSULTA: "NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl",  # noqa
        WS_NFE_SITUACAO: "NFeStatusServico4/NFeStatusServico4.asmx?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl",  # noqa
        WS_NFE_AUTORIZACAO: "NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl",
        WS_NFE_RET_AUTORIZACAO: "NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl",  # noqa
    },
}
SVAN[CTE_MODELO] = SVRS[CTE_MODELO]

SVC_AN = {
    AMBIENTE_PRODUCAO: {
        "servidor": "www.svc.fazenda.gov.br",
        WS_NFE_CONSULTA: "NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl",  # noqa
        WS_NFE_SITUACAO: "NFeStatusServico4/NFeStatusServico4.asmx?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl",  # noqa
        WS_NFE_AUTORIZACAO: "NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl",
        WS_NFE_RET_AUTORIZACAO: "NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl",  # noqa
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "hom.svc.fazenda.gov.br",
        WS_NFE_CONSULTA: "NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl",  # noqa
        WS_NFE_SITUACAO: "NFeStatusServico4/NFeStatusServico4.asmx?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl",  # noqa
        WS_NFE_AUTORIZACAO: "NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl",
        WS_NFE_RET_AUTORIZACAO: "NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl",  # noqa
    },
}

SVC_RS = {
    AMBIENTE_PRODUCAO: {
        "servidor": "nfe.svrs.rs.gov.br",
        WS_NFE_RECEPCAO_EVENTO: "ws/NfeConsulta/NfeConsulta4.asmx?wsdl",
        WS_NFE_AUTORIZACAO: "ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl",
        WS_NFE_RET_AUTORIZACAO: "ws/recepcaoevento/recepcaoevento4.asmx?wsdl",
        WS_NFE_CONSULTA: "ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
        WS_NFE_SITUACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "nfe-homologacao.svrs.rs.gov.br",
        WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta4.asmx?wsdl",
        WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento4.asmx?wsdl",
        WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
        WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl",  # noqa
    },
}

AN = {
    AMBIENTE_PRODUCAO: {
        "servidor": "www1.nfe.fazenda.gov.br",
        WS_DFE_DISTRIBUICAO: "NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl",
        WS_DOWNLOAD_NFE: "NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl",  # noqa
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "hom.nfe.fazenda.gov.br",
        WS_DFE_DISTRIBUICAO: "NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl",
        WS_DOWNLOAD_NFE: "NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?Wsdl",  # noqa
    },
}

UFBA = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfe.sefaz.ba.gov.br",
            WS_NFE_INUTILIZACAO: "webservices/NFeInutilizacao4/NFeInutilizacao4.asmx?wsdl",  # noqa
            WS_NFE_CONSULTA: "webservices/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl",  # noqa
            WS_NFE_SITUACAO: "webservices/NFeStatusServico4/NFeStatusServico4.asmx?wsdl",  # noqa
            WS_NFE_RECEPCAO_EVENTO: "webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl",  # noqa
            WS_NFE_AUTORIZACAO: "webservices/NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl",  # noqa
            WS_NFE_RET_AUTORIZACAO: "webservices/NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl",  # noqa
            WS_NFE_CADASTRO: "webservices/CadConsultaCadastro4/CadConsultaCadastro4.asmx?wsdl",  # noqa
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "hnfe.sefaz.ba.gov.br",
            WS_NFE_INUTILIZACAO: "webservices/NFeInutilizacao4/NFeInutilizacao4.asmx?wsdl",  # noqa
            WS_NFE_CONSULTA: "webservices/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl",  # noqa
            WS_NFE_SITUACAO: "webservices/NFeStatusServico4/NFeStatusServico4.asmx?wsdl",  # noqa
            WS_NFE_RECEPCAO_EVENTO: "webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl",  # noqa
            WS_NFE_AUTORIZACAO: "webservices/NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl",  # noqa
            WS_NFE_RET_AUTORIZACAO: "webservices/NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl",  # noqa
            WS_NFE_CADASTRO: "webservices/CadConsultaCadastro4/CadConsultaCadastro4.asmx?wsdl",  # noqa
        },
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfce.svrs.rs.gov.br",
            WS_NFE_INUTILIZACAO: "ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl",
            WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento4.asmx?wsdl",
            WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl",  # noqa
            WS_NFCE_QR_CODE: "http://dec.fazenda.df.gov.br/ConsultarNFCe.aspx?",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "nfce-homologacao.svrs.rs.gov.br",
            WS_NFE_INUTILIZACAO: "ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl",
            WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento4.asmx?wsdl",
            WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl",  # noqa
            WS_NFCE_QR_CODE: "http://dec.fazenda.df.gov.br/ConsultarNFCe.aspx?",
        },
    },
}

UFCE = {
    AMBIENTE_PRODUCAO: {
        "servidor": "nfe.sefaz.ce.gov.br",
        WS_NFE_INUTILIZACAO: "nfe4/services/NFeInutilizacao4?wsdl",
        WS_NFE_CONSULTA: "nfe4/services/NFeConsultaProtocolo4?wsdl",
        WS_NFE_SITUACAO: "nfe4/services/NFeStatusServico4?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "nfe4/services/NFeRecepcaoEvento4?wsdl",
        WS_NFE_AUTORIZACAO: "nfe4/services/NFeAutorizacao4?wsdl",
        WS_NFE_RET_AUTORIZACAO: "nfe4/services/NFeRetAutorizacao4?wsdl",
        WS_NFE_CADASTRO: "nfe4/services/CadConsultaCadastro4?wsdl",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "nfeh.sefaz.ce.gov.br",
        WS_NFE_INUTILIZACAO: "nfe4/services/NFeInutilizacao4?wsdl",
        WS_NFE_CONSULTA: "nfe4/services/NFeConsultaProtocolo4?wsdl",
        WS_NFE_SITUACAO: "nfe4/services/NFeStatusServico4?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "nfe4/services/NFeRecepcaoEvento4?wsdl",
        WS_NFE_AUTORIZACAO: "nfe4/services/NFeAutorizacao4?wsdl",
        WS_NFE_RET_AUTORIZACAO: "nfe4/services/NFeRetAutorizacao4?wsdl",
        WS_NFE_CADASTRO: "nfe4/services/CadConsultaCadastro4?wsdl",
    },
}
UFCE[CTE_MODELO] = SVRS[CTE_MODELO]


UFGO = {
    AMBIENTE_PRODUCAO: {
        "servidor": "nfe.sefaz.go.gov.br",
        WS_NFE_INUTILIZACAO: "nfe/services/NFeInutilizacao4?wsdl",
        WS_NFE_CONSULTA: "nfe/services/NFeConsultaProtocolo4?wsdl",
        WS_NFE_SITUACAO: "nfe/services/NFeStatusServico4?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "nfe/services/NFeRecepcaoEvento4?wsdl",
        WS_NFE_AUTORIZACAO: "nfe/services/NFeAutorizacao4?wsdl",
        WS_NFE_RET_AUTORIZACAO: "nfe/services/NFeRetAutorizacao4?wsdl",
        WS_NFE_CADASTRO: "nfe/services/CadConsultaCadastro4?wsdl",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "homolog.sefaz.go.gov.br",
        WS_NFE_INUTILIZACAO: "nfe/services/NFeInutilizacao4?wsdl",
        WS_NFE_CONSULTA: "nfe/services/NFeConsultaProtocolo4?wsdl",
        WS_NFE_SITUACAO: "nfe/services/NFeStatusServico4?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "nfe/services/NFeRecepcaoEvento4?wsdl",
        WS_NFE_AUTORIZACAO: "nfe/services/NFeAutorizacao4?wsdl",
        WS_NFE_RET_AUTORIZACAO: "nfe/services/NFeRetAutorizacao4?wsdl",
        WS_NFE_CADASTRO: "nfe/services/CadConsultaCadastro4?wsdl",
    },
}
UFGO[CTE_MODELO] = SVRS[CTE_MODELO]


UFMT = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfe.sefaz.mt.gov.br",
            WS_NFE_INUTILIZACAO: "nfews/v2/services/NfeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfews/v2/services/NfeConsulta4?wsdl",
            WS_NFE_SITUACAO: "nfews/v2/services/NfeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "nfews/v2/services/RecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfews/v2/services/NfeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfews/v2/services/NfeRetAutorizacao4?wsdl",
            WS_NFE_CADASTRO: "nfews/v2/services/CadConsultaCadastro4?wsdl",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homologacao.sefaz.mt.gov.br",
            WS_NFE_INUTILIZACAO: "nfews/v2/services/NfeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfews/v2/services/NfeConsulta4?wsdl",
            WS_NFE_SITUACAO: "nfews/v2/services/NfeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "nfews/v2/services/RecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfews/v2/services/NfeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfews/v2/services/NfeRetAutorizacao4?wsdl",
            WS_NFE_CADASTRO: "nfews/v2/services/CadConsultaCadastro4?wsdl",
        },
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfce.sefaz.mt.gov.br",
            WS_NFE_RECEPCAO_EVENTO: "nfcews/services/RecepcaoEvento4",
            WS_NFE_AUTORIZACAO: "nfcews/services/NfeAutorizacao4",
            WS_NFE_RET_AUTORIZACAO: "nfcews/services/NfeRetAutorizacao4",
            WS_NFE_INUTILIZACAO: "nfcews/services/NfeInutilizacao4",
            WS_NFE_CONSULTA: "nfcews/services/NfeConsulta4",
            WS_NFE_SITUACAO: "nfcews/services/NfeStatusServico4",
            WS_NFCE_QR_CODE: "http://www.sefaz.mt.gov.br/nfce/consultanfce",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homologacao.sefaz.mt.gov.br",
            WS_NFE_RECEPCAO_EVENTO: "nfcews/services/RecepcaoEvento4",
            WS_NFE_AUTORIZACAO: "nfcews/services/NfeAutorizacao4",
            WS_NFE_RET_AUTORIZACAO: "nfcews/services/NfeRetAutorizacao4",
            WS_NFE_INUTILIZACAO: "nfcews/services/NfeInutilizacao4",
            WS_NFE_CONSULTA: "nfcews/services/NfeConsulta4",
            WS_NFE_SITUACAO: "nfcews/services/NfeStatusServico4",
            WS_NFCE_QR_CODE: "http://www.sefaz.mt.gov.br/nfce/consultanfce",
        },
    },
    CTE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "cte.sefaz.mt.gov.br",
            WS_CTE400_RECEPCAO_SINC: "ctews2/services/CTeRecepcaoSincV4?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "ctews2/services/CTeRecepcaoGTVeV4?wsdl",
            WS_CTE400_RECEPCAO_OSV: "ctews/services/CTeRecepcaoOSV4?wsdl",
            WS_CTE400_CONSULTA: "ctews2/services/CTeConsultaV4?wsdl",
            WS_CTE400_STATUS_SERVICO: "ctews2/services/CTeStatusServicoV4?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "ctews2/services/CTeRecepcaoEventoV4?wsdl",
            WS_CTE400_QRCODE: "https://www.sefaz.mt.gov.br/cte/qrcode",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homologacao.sefaz.mt.gov.br",
            WS_CTE400_RECEPCAO_SINC: "ctews2/services/CTeRecepcaoSincV4?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "ctews2/services/CTeRecepcaoGTVeV4?wsdl",
            WS_CTE400_RECEPCAO_OSV: "ctews/services/CTeRecepcaoOSV4?wsdl",
            WS_CTE400_CONSULTA: "ctews2/services/CTeConsultaV4?wsdl",
            WS_CTE400_STATUS_SERVICO: "ctews2/services/CTeStatusServicoV4?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "ctews2/services/CTeRecepcaoEventoV4?wsdl",
            WS_CTE400_QRCODE: "https://www.sefaz.mt.gov.br/cte/qrcode",
        }
    }
}

UFMS = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfe.sefaz.ms.gov.br",
            WS_NFE_INUTILIZACAO: "ws/NFeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "ws/NFeConsultaProtocolo4?wsdl",
            WS_NFE_SITUACAO: "ws/NFeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/NFeRecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "ws/NFeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NFeRetAutorizacao4?wsdl",
            WS_NFE_CADASTRO: "ws/CadConsultaCadastro4?wsdl",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "hom.nfe.sefaz.ms.gov.br",
            WS_NFE_INUTILIZACAO: "ws/NFeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "ws/NFeConsultaProtocolo4?wsdl",
            WS_NFE_SITUACAO: "ws/NFeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/NFeRecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "ws/NFeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NFeRetAutorizacao4?wsdl",
            WS_NFE_CADASTRO: "ws/CadConsultaCadastro4?wsdl",
        },
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfce.sefaz.ms.gov.br",
            WS_NFE_RECEPCAO_EVENTO: "ws/NFeRecepcaoEvento4",
            WS_NFE_AUTORIZACAO: "ws/NFeAutorizacao4",
            WS_NFE_RET_AUTORIZACAO: "ws/NFeRetAutorizacao4",
            WS_NFE_CADASTRO: "CadConsultaCadastro4",
            WS_NFE_INUTILIZACAO: "ws/NFeInutilizacao4",
            WS_NFE_CONSULTA: "ws/NFeConsultaProtocolo4",
            WS_NFE_SITUACAO: "ws/NFeStatusServico4",
            WS_NFCE_QR_CODE: "www.dfe.ms.gov.br/nfce/qrcode?",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "hom.nfce.sefaz.ms.gov.br",
            WS_NFE_RECEPCAO_EVENTO: "ws/NFeRecepcaoEvento4",
            WS_NFE_AUTORIZACAO: "ws/NFeAutorizacao4",
            WS_NFE_RET_AUTORIZACAO: "ws/NFeRetAutorizacao4",
            WS_NFE_CADASTRO: "ws/CadConsultaCadastro4",
            WS_NFE_INUTILIZACAO: "ws/NFeInutilizacao4",
            WS_NFE_CONSULTA: "ws/NFeConsultaProtocolo4",
            WS_NFE_SITUACAO: "ws/NFeStatusServico4",
            WS_NFCE_QR_CODE: "www.dfe.ms.gov.br/nfce/qrcode?",
        },
    },
    CTE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "producao.cte.ms.gov.br",
            WS_CTE400_RECEPCAO_SINC: "ws/CTeRecepcaoSincV4?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "ws/CTeRecepcaoGTVeV4?wsdl",
            WS_CTE400_RECEPCAO_OSV: "ws/CTeRecepcaoOSV4?wsdl",
            WS_CTE400_CONSULTA: "ws/CTeConsultaV4?wsdl",
            WS_CTE400_STATUS_SERVICO: "ws/CTeStatusServicoV4?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "ws/CTeRecepcaoEventoV4?wsdl",
            WS_CTE400_QRCODE: "http://www.dfe.ms.gov.br/cte/qrcode",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homologacao.cte.ms.gov.br",
            WS_CTE400_RECEPCAO_SINC: "ws/CTeRecepcaoSincV4?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "ws/CTeRecepcaoGTVeV4?wsdl",
            WS_CTE400_RECEPCAO_OSV: "ws/CTeRecepcaoOSV4?wsdl",
            WS_CTE400_CONSULTA: "ws/CTeConsultaV4?wsdl",
            WS_CTE400_STATUS_SERVICO: "ws/CTeStatusServicoV4?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "ws/CTeRecepcaoEventoV4?wsdl",
            WS_CTE400_QRCODE: "http://www.dfe.ms.gov.br/cte/qrcode",
        }
    }
}

UFMG = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfe.fazenda.mg.gov.br",
            WS_NFE_INUTILIZACAO: "nfe2/services/NFeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfe2/services/NFeConsultaProtocolo4?wsdl",
            WS_NFE_SITUACAO: "nfe2/services/NFeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "nfe2/services/NFeRecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfe2/services/NFeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfe2/services/NFeRetAutorizacao4?wsdl",
            WS_NFE_CADASTRO: "nfe2/services/CadConsultaCadastro4?wsdl",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "hnfe.fazenda.mg.gov.br",
            WS_NFE_INUTILIZACAO: "nfe2/services/NFeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfe2/services/NFeConsultaProtocolo4?wsdl",
            WS_NFE_SITUACAO: "nfe2/services/NFeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "nfe2/services/NFeRecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfe2/services/NFeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfe2/services/NFeRetAutorizacao4?wsdl",
            WS_NFE_CADASTRO: "nfe2/services/CadConsultaCadastro4?wsdl",
        },
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfce.fazenda.mg.gov.br",
            WS_NFE_INUTILIZACAO: "nfce/services/NFeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfce/services/NFeConsultaProtocolo4?wsdl",
            WS_NFE_SITUACAO: "nfce/services/NFeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "nfce/services/NFeRecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfce/services/NFeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfce/services/NFeRetAutorizacao4?wsdl",
            WS_NFCE_QR_CODE: "nfce.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml?",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "hnfce.fazenda.mg.gov.br",
            WS_NFE_INUTILIZACAO: "nfce/services/NFeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfce/services/NFeConsultaProtocolo4?wsdl",
            WS_NFE_SITUACAO: "nfce/services/NFeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "nfce/services/NFeRecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfce/services/NFeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfce/services/NFeRetAutorizacao4?wsdl",
            WS_NFCE_QR_CODE: "nfce.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml?",
        },
    },
    CTE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "cte.fazenda.mg.gov.br",
            WS_CTE400_RECEPCAO_SINC: "cte/services/CTeRecepcaoSincV4?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "cte/services/CTeRecepcaoGTVeV4?wsdl",
            WS_CTE400_RECEPCAO_OSV: "cte/services/CTeRecepcaoOSV4?wsdl",
            WS_CTE400_CONSULTA: "cte/services/CTeConsultaV4?wsdl",
            WS_CTE400_STATUS_SERVICO: "cte/services/CTeStatusServicoV4?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "cte/services/CTeRecepcaoEventoV4?wsdl",
            WS_CTE400_QRCODE: "https://cte.fazenda.mg.gov.br/portalcte/sistema/qrcode.xhtml",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "hcte.fazenda.mg.gov.br",
            WS_CTE400_RECEPCAO_SINC: "cte/services/CTeRecepcaoSincV4?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "cte/services/CTeRecepcaoGTVeV4?wsdl",
            WS_CTE400_RECEPCAO_OSV: "cte/services/CTeRecepcaoOSV4?wsdl",
            WS_CTE400_CONSULTA: "cte/services/CTeConsultaV4?wsdl",
            WS_CTE400_STATUS_SERVICO: "cte/services/CTeStatusServicoV4?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "cte/services/CTeRecepcaoEventoV4?wsdl",
            WS_CTE400_QRCODE: "https://cte.fazenda.mg.gov.br/portalcte/sistema/qrcode.xhtml",
        }
    }
}

UFPR = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfe.sefa.pr.gov.br",
            WS_NFE_INUTILIZACAO: "nfe/NFeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfe/NFeConsultaProtocolo4?wsdl",
            WS_NFE_SITUACAO: "nfe/NFeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "nfe/NFeRecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfe/NFeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfe/NFeRetAutorizacao4?wsdl",
            WS_NFE_CADASTRO: "nfe/CadConsultaCadastro4?wsdl",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homologacao.nfe.sefa.pr.gov.br",
            WS_NFE_INUTILIZACAO: "nfe/NFeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfe/NFeConsultaProtocolo4?wsdl",
            WS_NFE_SITUACAO: "nfe/NFeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "nfe/NFeRecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfe/NFeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfe/NFeRetAutorizacao4?wsdl",
            WS_NFE_CADASTRO: "nfe/CadConsultaCadastro4?wsdl",
        },
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfce.sefa.pr.gov.br",
            WS_NFE_RECEPCAO_EVENTO: "nfce/NFeRecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfce/NFeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfce/NFeRetAutorizacao4?wsdl",
            WS_NFE_CADASTRO: "nfce/CadConsultaCadastro4?wsdl",
            WS_NFE_INUTILIZACAO: "nfce/NFeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfce/NFeConsultaProtocolo4?wsdl",
            WS_NFE_SITUACAO: "nfce/NFeStatusServico4?wsdl",
            WS_NFCE_QR_CODE: "www.fazenda.pr.gov.br/nfce/qrcode?",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homologacao.nfce.sefa.pr.gov.br",
            WS_NFE_RECEPCAO_EVENTO: "nfce/NFeRecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfce/NFeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfce/NFeRetAutorizacao4?wsdl",
            WS_NFE_CADASTRO: "nfce/CadConsultaCadastro4?wsdl",
            WS_NFE_INUTILIZACAO: "nfce/NFeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfce/NFeConsultaProtocolo4?wsdl",
            WS_NFE_SITUACAO: "nfce/NFeStatusServico4?wsdl",
            WS_NFCE_QR_CODE: "www.fazenda.pr.gov.br/nfce/qrcode?",
        },
    },
    CTE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "cte.fazenda.pr.gov.br",
            WS_CTE400_RECEPCAO_SINC: "cte4/CTeRecepcaoSincV4?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "cte4/CTeRecepcaoGTVeV4?wsdl",
            WS_CTE400_RECEPCAO_OSV: "cte4/CTeRecepcaoOSV4?wsdl",
            WS_CTE400_CONSULTA: "cte4/CTeConsultaV4?wsdl",
            WS_CTE400_STATUS_SERVICO: "cte4/CTeStatusServicoV4?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "cte4/CTeRecepcaoEventoV4?wsdl",
            WS_CTE400_QRCODE: "http://www.fazenda.pr.gov.br/cte/qrcode",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homologacao.cte.fazenda.pr.gov.br",
            WS_CTE400_RECEPCAO_SINC: "cte4/CTeRecepcaoSincV4?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "cte4/CTeRecepcaoGTVeV4?wsdl",
            WS_CTE400_RECEPCAO_OSV: "cte4/CTeRecepcaoOSV4?wsdl",
            WS_CTE400_CONSULTA: "cte4/CTeConsultaV4?wsdl",
            WS_CTE400_STATUS_SERVICO: "cte4/CTeStatusServicoV4?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "cte4/CTeRecepcaoEventoV4?wsdl",
            WS_CTE400_QRCODE: "http://www.fazenda.pr.gov.br/cte/qrcode",
        }
    }
}

UFRS = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfe.sefazrs.rs.gov.br",
            WS_NFE_INUTILIZACAO: "ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl",  # noqa
            WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento4.asmx?wsdl",  # noqa
            WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl",  # noqa
            WS_NFE_CADASTRO: "ws/cadconsultacadastro/cadconsultacadastro4.asmx?wsdl",  # noqa
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "nfe-homologacao.sefazrs.rs.gov.br",
            WS_NFE_INUTILIZACAO: "ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl",  # noqa
            WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento4.asmx?wsdl",  # noqa
            WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl",  # noqa
            WS_NFE_CADASTRO: "ws/cadconsultacadastro/cadconsultacadastro4.asmx?wsdl",  # noqa
        },
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfce.sefazrs.rs.gov.br",
            WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento.asmx",
            WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao.asmx",
            WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao.asmx",  # noqa
            WS_NFE_CADASTRO: "ws/cadconsultacadastro/cadconsultacadastro2.asmx",  # noqa
            WS_NFE_INUTILIZACAO: "ws/NfeInutilizacao/NfeInutilizacao2.asmx",
            WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta2.asmx",
            WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico2.asmx",
            WS_NFCE_QR_CODE: "https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "nfce-homologacao.sefazrs.rs.gov.br",
            WS_NFE_RECEPCAO_EVENTO: "ws/recepcaoevento/recepcaoevento.asmx",
            WS_NFE_AUTORIZACAO: "ws/NfeAutorizacao/NFeAutorizacao.asmx",
            WS_NFE_RET_AUTORIZACAO: "ws/NfeRetAutorizacao/NFeRetAutorizacao.asmx",  # noqa
            WS_NFE_CADASTRO: "ws/cadconsultacadastro/cadconsultacadastro2.asmx",  # noqa
            WS_NFE_INUTILIZACAO: "ws/NfeInutilizacao/NfeInutilizacao2.asmx",
            WS_NFE_CONSULTA: "ws/NfeConsulta/NfeConsulta2.asmx",
            WS_NFE_SITUACAO: "ws/NfeStatusServico/NfeStatusServico2.asmx",
            WS_NFCE_QR_CODE: "https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx",
        },
    },
}
UFRS[CTE_MODELO] = SVRS[CTE_MODELO]

UFSP = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfe.fazenda.sp.gov.br",
            WS_NFE_INUTILIZACAO: "ws/nfeinutilizacao4.asmx?wsdl",
            WS_NFE_CONSULTA: "ws/nfeconsultaprotocolo4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/nfestatusservico4.asmx?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/nferecepcaoevento4.asmx?wsdl",
            WS_NFE_AUTORIZACAO: "ws/nfeautorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/nferetautorizacao4.asmx?wsdl",
            WS_NFE_CADASTRO: "ws/cadconsultacadastro4.asmx?wsdl",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homologacao.nfe.fazenda.sp.gov.br",
            WS_NFE_INUTILIZACAO: "ws/nfeinutilizacao4.asmx?wsdl",
            WS_NFE_CONSULTA: "ws/nfeconsultaprotocolo4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/nfestatusservico4.asmx?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "ws/nferecepcaoevento4.asmx?wsdl",
            WS_NFE_AUTORIZACAO: "ws/nfeautorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/nferetautorizacao4.asmx?wsdl",
            WS_NFE_CADASTRO: "ws/cadconsultacadastro4.asmx?wsdl",
        },
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfce.fazenda.sp.gov.br",
            WS_NFE_AUTORIZACAO: "ws/NFeAutorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NFeRetAutorizacao4.asmx?wsdl",
            WS_NFE_INUTILIZACAO: "ws/NFeInutilizacao4.asmx?wsdl",
            WS_NFE_CONSULTA: "ws/NFeConsultaProtocolo4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/NFeStatusServico4.asmx?wsdl",
            WS_NFE_CADASTRO: "ws/cadconsultacadastro2.asmx",
            WS_NFE_RECEPCAO_EVENTO: "ws/NFeRecepcaoEvento4.asmx?wsdl",
            WS_NFCE_QR_CODE: "",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homologacao.nfce.fazenda.sp.gov.br",
            WS_NFE_AUTORIZACAO: "ws/NFeAutorizacao4.asmx?wsdl",
            WS_NFE_RET_AUTORIZACAO: "ws/NFeRetAutorizacao4.asmx?wsdl",
            WS_NFE_INUTILIZACAO: "ws/NFeInutilizacao4.asmx?wsdl",
            WS_NFE_CONSULTA: "ws/NFeConsultaProtocolo4.asmx?wsdl",
            WS_NFE_SITUACAO: "ws/NFeStatusServico4.asmx?wsdl",
            WS_NFE_CADASTRO: "ws/cadconsultacadastro2.asmx",
            WS_NFE_RECEPCAO_EVENTO: "ws/NFeRecepcaoEvento4.asmx?wsdl",
            WS_NFCE_QR_CODE: "https://homologacao.nfce.fazenda.sp.gov.br/NFCEConsultaPublica/Paginas/ConstultaQRCode.aspx",
        },
    },
    CTE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfe.fazenda.sp.gov.br",
            WS_CTE400_RECEPCAO_SINC: "cteWS/WS/CTeRecepcaoSincV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "cteWS/WS/CTeRecepcaoGTVeV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_OSV: "cteWS/WS/CTeRecepcaoOSV4.asmx?wsdl",
            WS_CTE400_CONSULTA: "cteWS/WS/CTeConsultaV4.asmx?wsdl",
            WS_CTE400_STATUS_SERVICO: "cteWS/WS/CTeStatusServicoV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "cteWS/WS/CTeRecepcaoEventoV4.asmx?wsdl",
            WS_CTE400_QRCODE: "https://nfe.fazenda.sp.gov.br/CTeConsulta/qrCode",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homologacao.nfe.fazenda.sp.gov.br",
            WS_CTE400_RECEPCAO_SINC: "cteWS/WS/CTeRecepcaoSincV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_GTVE: "cteWS/WS/CTeRecepcaoGTVeV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_OSV: "cteWS/WS/CTeRecepcaoOSV4.asmx?wsdl",
            WS_CTE400_CONSULTA: "cteWS/WS/CTeConsultaV4.asmx?wsdl",
            WS_CTE400_STATUS_SERVICO: "cteWS/WS/CTeStatusServicoV4.asmx?wsdl",
            WS_CTE400_RECEPCAO_EVENTO: "cteWS/WS/CTeRecepcaoEventoV4.asmx?wsdl",
            WS_CTE400_QRCODE: "https://nfe.fazenda.sp.gov.br/CTeConsulta/qrCode",
        }
    }
}

UFPE = {
    AMBIENTE_PRODUCAO: {
        "servidor": "nfe.sefaz.pe.gov.br",
        WS_NFE_INUTILIZACAO: "nfe-service/services/NFeInutilizacao4?wsdl",
        WS_NFE_CONSULTA: "nfe-service/services/NFeConsultaProtocolo4?wsdl",
        WS_NFE_SITUACAO: "nfe-service/services/NFeStatusServico4?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "nfe-service/services/NFeRecepcaoEvento4?wsdl",
        WS_NFE_AUTORIZACAO: "nfe-service/services/NFeAutorizacao4?Wsdl",
        WS_NFE_RET_AUTORIZACAO: "nfe-service/services/NFeRetAutorizacao4?wsdl",
        WS_NFE_CADASTRO: "nfe-service/services/CadConsultaCadastro2?wsdl",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "nfehomolog.sefaz.pe.gov.br",
        WS_NFE_INUTILIZACAO: "nfe-service/services/NFeInutilizacao4?wsdl",
        WS_NFE_CONSULTA: "nfe-service/services/NFeConsultaProtocolo4?wsdl",
        WS_NFE_SITUACAO: "nfe-service/services/NFeStatusServico4?wsdl",
        WS_NFE_RECEPCAO_EVENTO: "nfe-service/services/NFeRecepcaoEvento4?wsdl",
        WS_NFE_AUTORIZACAO: "nfe-service/services/NFeAutorizacao4?wsdl",
        WS_NFE_RET_AUTORIZACAO: "nfe-service/services/NFeRetAutorizacao4?wsdl",
        WS_NFE_CADASTRO: "nfe-service/services/CadConsultaCadastro2?wsdl",
    },
}
UFPE[CTE_MODELO] = UFSP[CTE_MODELO]

UFRR = SVRS
UFRR[CTE_MODELO] = UFSP[CTE_MODELO]

UFAM = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfe.sefaz.am.gov.br",
            WS_NFE_INUTILIZACAO: "services2/services/NfeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "services2/services/NfeConsulta4?wsdl",
            WS_NFE_SITUACAO: "services2/services/NfeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "services2/services/RecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "services2/services/NfeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "services2/services/NfeRetAutorizacao4?wsdl",  # noqa
            WS_NFE_CADASTRO: "services2/services/cadconsultacadastro2?wsdl",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homnfe.sefaz.am.gov.br",
            WS_NFE_INUTILIZACAO: "services2/services/NfeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "services2/services/NfeConsulta4?wsdl",
            WS_NFE_SITUACAO: "services2/services/NfeStatusServico4?wsdl",
            WS_NFE_RECEPCAO_EVENTO: "services2/services/RecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "services2/services/NfeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "services2/services/NfeRetAutorizacao4?wsdl",  # noqa
            WS_NFE_CADASTRO: "services2/services/cadconsultacadastro2?wsdl",
        },
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            "servidor": "nfce.sefaz.am.gov.br",
            WS_NFE_RECEPCAO_EVENTO: "nfce-services/services/RecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfce-services/services/NfeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfce-services/services/NfeRetAutorizacao4?wsdl",
            WS_NFE_INUTILIZACAO: "nfce-services/services/NfeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfce-services/services/NfeConsulta4?wsdl",
            WS_NFE_SITUACAO: "nfce-services/services/NfeStatusServico4?wsdl",
        },
        AMBIENTE_HOMOLOGACAO: {
            "servidor": "homnfce.sefaz.am.gov.br",
            WS_NFE_RECEPCAO_EVENTO: "nfce-services/services/RecepcaoEvento4?wsdl",
            WS_NFE_AUTORIZACAO: "nfce-services/services/NfeAutorizacao4?wsdl",
            WS_NFE_RET_AUTORIZACAO: "nfce-services/services/NfeRetAutorizacao4?wsdl",
            WS_NFE_INUTILIZACAO: "nfce-services/services/NfeInutilizacao4?wsdl",
            WS_NFE_CONSULTA: "nfce-services/services/NfeConsulta4?wsdl",
            WS_NFE_SITUACAO: "nfce-services/services/NfeStatusServico4?wsdl",
            WS_NFCE_QR_CODE: "http://homnfce.sefaz.am.gov.br/nfceweb/consultarNFCe.jsp",
        },
    },
}
UFAM[CTE_MODELO] = SVRS[CTE_MODELO]


ESTADO_WS = {
    "AC": SVRS,
    "AL": SVRS,
    "AM": UFAM,
    "AP": SVRS,
    "BA": UFBA,
    "CE": UFCE,
    "DF": SVRS,
    "ES": SVRS,
    "GO": UFGO,
    "MA": SVAN,
    "MG": UFMG,
    "MS": UFMS,
    "MT": UFMT,
    "PA": SVAN,
    "PB": SVRS,
    "PE": UFPE,
    "PI": SVAN,
    "PR": UFPR,
    "RJ": SVRS,
    "RN": SVRS,
    "RO": SVRS,
    "RR": UFRR,
    "RS": UFRS,
    "SC": SVRS,
    "SE": SVRS,
    "SP": UFSP,
    "TO": SVRS,
    "AN": AN,
}
