# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import re
import csv
from datetime import date, datetime
import lxml.etree as ET
from unicodedata import normalize
from pytrustnfe.Servidores import ESTADO_WS,SIGLA_ESTADO


def ibge2siafi(ibge_or_cnpj):
    try:
        path = os.path.dirname(__file__)
        with open(path + '/data/csvs/tab_siafi_20220106.csv', 'r') as file:
            for row in csv.reader(file, delimiter=";"):
                if str(row[4]).strip() == str(ibge_or_cnpj).strip() or \
                   str(row[1]).strip() == str(ibge_or_cnpj).strip():
                    return str(row[0]).strip()
    except Exception as e:
        print(e)
    return None

NFCOM_V100_ER = [
    "", #Vazio para fins de skip indice 0
    "(((20(([02468][048])|([13579][26]))-02-29))|(20[0-9][0-9])-((((0[1-9])|(1[0-2]))-((0[1-9])|(1\d)|(2[0-8])))|((((0[13578])|(1[02]))-31)|(((0[1,3-9])|(1[0-2]))-(29|30)))))T(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d([\-,\+](0[0-9]|10|11):00|([\+](12):00))",
    "[0-9]{7}",
    "[0-9]{44}",
    "[0-9]{36}",
    "[0-9]{16}",
    "[0-9]{3}",
    "[0-9]{14}",
    "[0-9]{3,14}",
    "[0-9]{0}|[0-9]{14}",
    "[0-9]{11}",
    "[0-9]{3,11}",
    "0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,2}(\.[0-9]{2})?",
    "0\.[0-9]{2}|[1-9]{1}[0-9]{0,2}(\.[0-9]{2})?",
    "0|0\.[0-9]{3}|[1-9]{1}[0-9]{0,2}(\.[0-9]{3})?",
    "0\.[0-9]{3}|[1-9]{1}[0-9]{0,2}(\.[0-9]{3})?",
    "[0-9]{1,3}(\.[0-9]{2,3})?",
    "0|0\.[0-9]{2,4}|[1-9]{1}[0-9]{0,2}(\.[0-9]{2,4})?",
    "0\.[0-9]{2,4}|[1-9]{1}[0-9]{0,2}(\.[0-9]{2,4})?",
    "0(\.[0-9]{2,4})?|[1-9]{1}[0-9]{0,1}(\.[0-9]{2,4})?|100(\.0{2,4})?",
    "[0-9]{1,4}(\.[0-9]{2,8})?",
    "0|0\.[0-9]{3}|[1-9]{1}[0-9]{0,4}(\.[0-9]{3})?",
    "0|0\.[0-9]{3}|[1-9]{1}[0-9]{0,7}(\.[0-9]{3})?",
    "0\.[0-9]{3}|[1-9]{1}[0-9]{0,7}(\.[0-9]{3})?",
    "0|0\.[0-9]{4}|[1-9]{1}[0-9]{0,7}(\.[0-9]{4})?",
    "0\.[0-9]{4}|[1-9]{1}[0-9]{0,7}(\.[0-9]{4})?",
    "0|0\.[0-9]{6}|[1-9]{1}[0-9]{0,8}(\.[0-9]{6})?",
    "0\.[0-9]{6}|[1-9]{1}[0-9]{0,8}(\.[0-9]{6})?",
    "0|0\.[0-9]{8}|[1-9]{1}[0-9]{0,8}(\.[0-9]{8})?",
    "0\.[0-9]{8}|[1-9]{1}[0-9]{0,8}(\.[0-9]{8})?",
    "0|0\.[0-9]{4}|[1-9]{1}[0-9]{0,10}(\.[0-9]{4})?",
    "0\.[0-9]{4}|[1-9]{1}[0-9]{0,10}(\.[0-9]{4})?",
    "[0-9]{1,11}(\.[0-9]{2,4})?",
    "0|0\.[0-9]{3}|[1-9]{1}[0-9]{0,11}(\.[0-9]{3})?",
    "0\.[0-9]{3}|[1-9]{1}[0-9]{0,11}(\.[0-9]{3})?",
    "0|0\.[0-9]{4}|[1-9]{1}[0-9]{0,11}(\.[0-9]{4})?",
    "0\.[0-9]{4}|[1-9]{1}[0-9]{0,11}(\.[0-9]{4})? ",
    "0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{2})?",
    "0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{2})?",
    "[0-9]{1,13}(\.[0-9]{2,6})?",
    "[0-9]{1,13}(\.[0-9]{2,8})?",
    "[0-9]{1,13}(\.[0-9]{2,4})?",
    "[0-9]{0,14}|ISENTO",
    "[0-9]{2,14}",
    "[1-9]{1}[0-9]{0,8}",
    "0|[1-9]{1}[0-9]{0,2}",
    "[0-9]{2}",
    "[0-9]{1,4}",
    "[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
    "((((20|19|18)(([02468][048])|([13579][26]))-02-29))|((20|19|18)[0-9][0-9])-((((0[1-9])|(1[0-2]))-((0[1-9])|(1\d)|(2[0-8])))|((((0[13578])|(1[02]))-31)|(((0[1,3-9])|(1[0-2]))-(29|30)))))",
    "[0-9]\.[0-9]{6}|[1-8][0-9]\.[0-9]{6}|90\.[0-9]{6}|-[0-9]\.[0-9]{6}|-[1-8][0-9]\.[0-9]{6}|-90\.[0-9]{6}",
    "[0-9]\.[0-9]{6}|[1-9][0-9]\.[0-9]{6}|1[0-7][0-9]\.[0-9]{6}|180\.[0-9]{6}|-[0-9]\.[0-9]{6}|-[1-9][0-9]\.[0-9]{6}|-1[0-7][0-9]\.[0-9]{6}|-180\.[0-9]{6}",
    "[0-9]{15}",
    "(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])",
    "[0-9]{8}",
    "[0-9]{1}",
    "([!-ÿ]{0}|[!-ÿ]{2,20})?",
    "([!-ÿ]{0}|[!-ÿ]{1,15})?",
    "[0-9]{7,12}",
    "[1-9]{1}[0-9]{0,1}|[1-8]{1}[0-9]{2}|[9]{1}[0-8]{1}[0-9]{1}|[9]{1}[9]{1}[0]{1}",
    "[0-9]{1,20}",
    "[0-9]{1,48}",
    "NFCom[0-9]{44}",
    "((HTTPS?|https?):\/\/.*\?chNFCom=[0-9]{44}&tpAmb=[1-2](&sign=[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1})?)",
    "[0-9]{1,15}",
    "1\.00",
    "(([0-1][0-9])|([2][0-3])):([0-5][0-9]):([0-5][0-9])",
    "[^@]+@[^\.]+\..+",
    "[123567][0-9]([0-9][1-9]|[1-9][0-9])",
    "[0-9]{1,6} ",
]

def date_tostring(data):
    assert isinstance(data, date), "Objeto date requerido"
    return data.strftime("%d-%m-%y")

def datetime_tostring(data):
    assert isinstance(data, datetime), "Objeto datetime requerido"
    return data.strftime("%d-%m-%y %H:%M:%S")

def _find_node(xml, node):
    for item in xml.iterchildren("*"):
        if node in item.tag:
            return item
        else:
            item = _find_node(item, node)
            if item is not None:
                return item
    return None

def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII','ignore').decode('ASCII')


class ChaveNFe(object):
    def __init__(self, **kwargs):
        self.cnpj = kwargs.pop("cnpj", "")
        self.estado = kwargs.pop("estado", "")
        self.emissao = kwargs.pop("emissao", "")
        self.modelo = kwargs.pop("modelo", "")
        self.serie = kwargs.pop("serie", "")
        self.numero = kwargs.pop("numero", "")
        self.tipo = kwargs.pop("tipo", "")
        self.codigo = kwargs.pop("codigo", "")

    def validar(self):
        assert self.cnpj != "", "CNPJ necessário para criar chave NF-e"
        assert self.estado != "", "Estado necessário para criar chave NF-e"
        assert self.emissao != "", "Emissão necessário para criar chave NF-e"
        assert self.modelo != "", "Modelo necessário para criar chave NF-e"
        assert self.serie != "", "Série necessária para criar chave NF-e"
        assert self.numero != "", "Número necessário para criar chave NF-e"
        assert self.tipo != "", "Tipo necessário para criar chave NF-e"
        assert self.codigo != "", "Código necessário para criar chave NF-e"


class ChaveNFCom(object):
    def __init__(self, **kwargs):
        self.estado = kwargs.pop("estado", "")
        self.emissao = kwargs.pop("emissao", "")
        self.cnpj = kwargs.pop("cnpj", "")
        self.modelo = kwargs.pop("modelo", "")
        self.serie = kwargs.pop("serie", "")
        self.numero = kwargs.pop("numero", "")
        self.tipo = kwargs.pop("tipo", "")
        self.site_aut = kwargs.pop("site_aut", "")
        self.codigo = kwargs.pop("codigo", "")

    def validar(self):
        assert self.cnpj != "", "CNPJ necessário para criar chave NFCom"
        assert self.estado != "", "Estado necessário para criar chave NFCom"
        assert self.emissao != "", "Emissão necessário para criar chave NFCom"
        assert self.modelo != "", "Modelo necessário para criar chave NFCom"
        assert self.serie != "", "Série necessária para criar chave NFCom"
        assert self.numero != "", "Número necessário para criar chave NFCom"
        assert self.tipo != "", "Tipo necessário para criar chave NFCom"
        assert self.site_aut != "", "Site Autorizador necessário para criar chave NFCom"
        assert self.codigo != "", "Código necessário para criar chave NFCom"


class ChaveCTe(object):
    def __init__(self, **kwargs):
        self.cnpj = kwargs.pop("cnpj", "")
        self.estado = kwargs.pop("estado", "")
        self.emissao = kwargs.pop("emissao", "")
        self.modelo = kwargs.pop("modelo", "")
        self.serie = kwargs.pop("serie", "")
        self.numero = kwargs.pop("numero", "")
        self.tipo = kwargs.pop("tipo", "")
        self.codigo = kwargs.pop("codigo", "")

    def validar(self):
        assert self.cnpj != "", "CNPJ necessário para criar chave CT-e"
        assert self.estado != "", "Estado necessário para criar chave CT-e"
        assert self.emissao != "", "Emissão necessário para criar chave CT-e"
        assert self.modelo != "", "Modelo necessário para criar chave CT-e"
        assert self.serie != "", "Série necessária para criar chave CT-e"
        assert self.numero != "", "Número necessário para criar chave CT-e"
        assert self.tipo != "", "Tipo necessário para criar chave CT-e"
        assert self.codigo != "", "Código necessário para criar chave CT-e"

class ChaveNFCom(object):
    def __init__(self, **kwargs):
        self.estado = kwargs.pop("estado", "")
        self.emissao = kwargs.pop("emissao", "")
        self.cnpj = kwargs.pop("cnpj", "")
        self.modelo = kwargs.pop("modelo", "")
        self.serie = kwargs.pop("serie", "")
        self.numero = kwargs.pop("numero", "")
        self.tipo = kwargs.pop("tipo", "")
        self.site_aut = kwargs.pop("site_aut", "")
        self.codigo = kwargs.pop("codigo", "")

    def validar(self):
        assert self.cnpj != "", "CNPJ necessário para criar chave NFCom"
        assert self.estado != "", "Estado necessário para criar chave NFCom"
        assert self.emissao != "", "Emissão necessário para criar chave NFCom"
        assert self.modelo != "", "Modelo necessário para criar chave NFCom"
        assert self.serie != "", "Série necessária para criar chave NFCom"
        assert self.numero != "", "Número necessário para criar chave NFCom"
        assert self.tipo != "", "Tipo necessário para criar chave NFCom"
        assert self.site_aut != "", "Site Autorizador necessário para criar chave NFCom"
        assert self.codigo != "", "Código necessário para criar chave NFCom"


class ChaveNFSeNacional(object):
    def __init__(self, **kwargs):
        self.ibge_mun = kwargs.pop("ibge_mun", "")
        self.ambiente = kwargs.pop("ambiente", "")
        self.tipo_insc_fed = kwargs.pop("tipo_insc_fed", "") #1 = CPF, 2 = CNPJ
        self.insc_fed = kwargs.pop("insc_fed", "")
        self.numero = kwargs.pop("numero", "")
        self.dt_emissao = kwargs.pop("dt_emissao", "")
        self.codigo = kwargs.pop("codigo", "")

    def validar(self):
        assert self.ibge_mun != "", "Código IBGE da Cidade é necessário para criar chave NFSe"
        assert self.ambiente != "", "Ambiente Gerador é necessário para criar chave NFSe"
        assert self.tipo_insc_fed != "", "Tipo de Inscrição Federal necessário para criar chave NFSe"
        assert self.insc_fed != "", "Inscrição Federal (CPF/CNPJ) necessário para criar chave NFSe"
        assert self.numero != "", "Número da NFSe é necessário para criar chave NFSe"
        assert self.dt_emissao != "", "Ano/Mês de emissão é necessário para criar chave NFSe"
        assert self.codigo != "", "Código é necessário para criar chave NFSe"


class ChaveNFSeNacionalDPS(object):
    def __init__(self, **kwargs):
        self.ibge_mun = kwargs.pop("ibge_mun", "")
        self.tipo_insc_fed = kwargs.pop("tipo_insc_fed", "") #1 = CPF, 2 = CNPJ
        self.insc_fed = kwargs.pop("insc_fed", "")
        self.serie = kwargs.pop("serie", "")
        self.numero = kwargs.pop("numero", "")

    def validar(self):
        assert self.ibge_mun != "", "Código IBGE da Cidade é necessário para criar chave NFSe DPS"
        assert self.tipo_insc_fed != "", "Tipo de Inscrição Federal necessário para criar chave NFSe DPS"
        assert self.insc_fed != "", "Inscrição Federal (CPF/CNPJ) necessário para criar chave NFSe DPS"
        assert self.serie != "", "Série é necessário para criar chave NFSe DPS"
        assert self.numero != "", "Número da NFSe é necessário para criar chave NFSe DPS"


class ChaveNFSeNacionalEvento(object):
    def __init__(self, **kwargs):
        self.id_pedido = kwargs.pop("id_pedido", "")
        self.nseq_evento = kwargs.pop("nseq_evento", "")

    def validar(self):
        assert self.id_pedido != "", "ID do pedido é necessário para criar chave de Evento"
        assert self.nseq_evento != "", "Número sequencial do evento é necessário para criar chave de Evento"


class ChaveNFSeNacionalPedidoRegistro(object):
    def __init__(self, **kwargs):
        self.chave_acesso = kwargs.pop("chave_acesso", "")
        self.cod_evento = kwargs.pop("cod_evento", "")
        self.nPedRegEvento = kwargs.pop("nPedRegEvento", "")

    def validar(self):
        assert self.chave_acesso != "", "Chave de Acesso da NFSe é necessário para criar chave de Pedido de Registro"
        assert self.cod_evento != "", "Código do evento é necessário para criar chave de Pedido de Registro"
        assert self.nPedRegEvento != "", "Número do Pedido de Registro do Evento é necessário para criar chave de Pedido de Registro"


def date_tostring(data):
    assert isinstance(data, date), "Objeto date requerido"
    return data.strftime("%d-%m-%y")


def nfcom_valor(valor):
    return str("%.2f" %(round(valor,2)))

def nfcom_qrcode(chNFCom, tpAmb, sigla, offline=False, assinatura=""):
    if offline:
        return "https://%s/Nfcom/QrCode?chNFCom=%s&tpAmb=%d&amp;sign=%s" %(ESTADO_WS[SIGLA_ESTADO[str(sigla)]]["62"][tpAmb]["QRCode"],chNFCom,tpAmb,assinatura)
    return "https://%s/Nfcom/QrCode?chNFCom=%s&amp;tpAmb=%d" %(ESTADO_WS[SIGLA_ESTADO[str(sigla)]]["62"][tpAmb]["QRCode"],chNFCom,tpAmb)

def gerar_chave_nfcom(obj_chave):
    assert isinstance(obj_chave, ChaveNFCom), "Objeto deve ser do tipo ChaveNFe"

def validar_dv(chave,dv):
    pesos = [4,3,2,9,8,7,6,5,4,3,2,9,8,7,6,5,4,3,2,9,8,7,6,5,4,3,2,9,8,7,6,5,4,3,2,9,8,7,6,5,4,3,2]
    sum = 0
    i = 0
    for c in chave:
        sum += int(c)*pesos[i]
        i += 1
    return dv == (11-(sum%11))

def gerar_chave_nfsenacional(obj_chave, prefix="NFS"):
    assert isinstance(obj_chave, ChaveNFSeNacional), "Objeto deve ser do tipo ChaveNFSeNacional"
    obj_chave.validar()
    chave_parcial = "%s%s%s%s%s%s%s" % (
        obj_chave.ibge_mun,
        obj_chave.ambiente,
        obj_chave.tipo_insc_fed,
        obj_chave.insc_fed.zfill(14),
        str(obj_chave.numero).zfill(13),
        obj_chave.dt_emissao,
        obj_chave.codigo,
    )
    chave_parcial = re.sub("[^0-9]", "", chave_parcial)
    soma = sum(int(a)*b for a, b in zip(reversed(chave_parcial), range(2, 9, 1)))
    dv = (11 - soma % 11) if (soma % 11 != 0 and soma % 11 != 1) else 0
    if prefix:
        return prefix + chave_parcial + str(dv)
    return chave_parcial + str(dv)


def gerar_chave_nfsenacional_dps(obj_chave, prefix="DPS"):
    assert isinstance(obj_chave, ChaveNFSeNacionalDPS), "Objeto deve ser do tipo ChaveNFSeNacionalDPS"
    obj_chave.validar()
    chave_parcial = "%s%d%s%s%s" % (
        obj_chave.ibge_mun,
        obj_chave.tipo_insc_fed,
        obj_chave.insc_fed.zfill(14),
        obj_chave.serie.zfill(5),
        str(obj_chave.numero).zfill(15),
    )
    return prefix + chave_parcial


def gerar_chave_nfsenacional_evento(obj_chave, prefix="EVT"):
    assert isinstance(obj_chave, ChaveNFSeNacionalEvento), "Objeto deve ser do tipo ChaveNFSeNacionalEvento"
    obj_chave.validar()
    chave_parcial = "%s%s" % (
        str(obj_chave.id_pedido).zfill(50),
        str(obj_chave.nseq_evento).zfill(3),
    )
    return prefix + chave_parcial


def gerar_chave_nfsenacional_pedido_registro(obj_chave, prefix="PRE"):
    assert isinstance(obj_chave, ChaveNFSeNacionalPedidoRegistro), "Objeto deve ser do tipo ChaveNFSeNacionalPedidoRegistro"
    obj_chave.validar()
    chave_parcial = "%s%s%s" % (
        str(obj_chave.chave_acesso),
        str(obj_chave.cod_evento).zfill(6),
        str(obj_chave.nPedRegEvento).zfill(3),
    )
    return prefix + chave_parcial


def gerar_chave_nfcom(obj_chave, prefix="NFCom"):
    assert isinstance(obj_chave, ChaveNFCom), "Objeto deve ser do tipo ChaveNFCom"
    obj_chave.validar()
    chave_parcial = "%s%s%s%s%s%s%d%d%s" % (
        obj_chave.estado,
        obj_chave.emissao,
        obj_chave.cnpj,
        obj_chave.modelo,
        str(obj_chave.serie).zfill(3),
        str(obj_chave.numero).zfill(9),
        obj_chave.tipo,
        obj_chave.site_aut,
        obj_chave.codigo.zfill(7),
    )
    chave_parcial = re.sub("[^0-9]", "", chave_parcial)
    soma = 0
    contador = 2
    for c in reversed(chave_parcial):
        soma += int(c) * contador
        contador += 1
        if contador == 10:
            contador = 2
    dv = (11 - soma % 11) if (soma % 11 != 0 and soma % 11 != 1) else 0
    if prefix:
        return prefix + chave_parcial + str(dv)
    return chave_parcial + str(dv)

def gerar_chave_cte(obj_chave, prefix=None):
    assert isinstance(obj_chave, ChaveCTe), "Objeto deve ser do tipo ChaveCTe"
    obj_chave.validar()
    chave_parcial = "%s%s%s%s%s%s%d%s" % (
        obj_chave.estado,
        obj_chave.emissao,
        obj_chave.cnpj,
        obj_chave.modelo,
        obj_chave.serie.zfill(3),
        str(obj_chave.numero).zfill(9),
        obj_chave.tipo,
        obj_chave.codigo,
    )
    chave_parcial = re.sub("[^0-9]", "", chave_parcial)
    soma = 0
    contador = 2
    for c in reversed(chave_parcial):
        soma += int(c) * contador
        contador += 1
        if contador == 10:
            contador = 2
    dv = (11 - soma % 11) if (soma % 11 != 0 and soma % 11 != 1) else 0
    if prefix:
        return prefix + chave_parcial + str(dv)
    return chave_parcial + str(dv)


def gerar_chave(obj_chave, prefix=None):
    assert isinstance(obj_chave, ChaveNFe), "Objeto deve ser do tipo ChaveNFe"
    obj_chave.validar()
    chave_parcial = "%s%s%s%s%s%s%d%s" % (
        obj_chave.estado,
        obj_chave.emissao,
        obj_chave.cnpj,
        obj_chave.modelo,
        obj_chave.serie.zfill(3),
        str(obj_chave.numero).zfill(9),
        obj_chave.tipo,
        obj_chave.codigo,
    )
    chave_parcial = re.sub("[^0-9]", "", chave_parcial)
    soma = 0
    contador = 2
    for c in reversed(chave_parcial):
        soma += int(c) * contador
        contador += 1
        if contador == 10:
            contador = 2
    dv = (11 - soma % 11) if (soma % 11 != 0 and soma % 11 != 1) else 0
    if prefix:
        return prefix + chave_parcial + str(dv)
    return chave_parcial + str(dv)

def _find_node(xml, node):
    for item in xml.iterchildren("*"):
        if node in item.tag:
            return item
        else:
            item = _find_node(item, node)
            if item is not None:
                return item
    return None


def gerar_nfeproc(envio, recibo):
    NSMAP = {None: "http://www.portalfiscal.inf.br/nfe"}
    root = ET.Element("nfeProc", versao="4.00", nsmap=NSMAP)
    parser = ET.XMLParser(encoding="utf-8")
    docEnvio = ET.fromstring(envio.encode("utf-8"), parser=parser)
    docRecibo = ET.fromstring(recibo.encode("utf-8"), parser=parser)

    nfe = _find_node(docEnvio, "NFe")
    protocolo = _find_node(docRecibo, "protNFe")
    if nfe is None or protocolo is None:
        return b""
    root.append(nfe)
    root.append(protocolo)
    return ET.tostring(root)


def gerar_nfeproc_cancel(nfe_proc, cancelamento):
    docEnvio = ET.fromstring(nfe_proc)
    docCancel = ET.fromstring(cancelamento)

    ev_cancelamento = _find_node(docCancel, "retEvento")
    if ev_cancelamento is None:
        return b""
    docEnvio.append(ev_cancelamento)
    return ET.tostring(docEnvio)


def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII','ignore').decode('ASCII')