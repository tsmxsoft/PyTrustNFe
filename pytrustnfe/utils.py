# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import re
from datetime import date, datetime
import lxml.etree as ET
from unicodedata import normalize


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

def date_tostring(data):
    assert isinstance(data, date), "Objeto date requerido"
    return data.strftime("%d-%m-%y")


def datetime_tostring(data):
    assert isinstance(data, datetime), "Objeto datetime requerido"
    return data.strftime("%d-%m-%y %H:%M:%S")


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
    dv = 11 - (soma%11)
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

def gerar_chave_nfcom(obj_chave, suffix="NFCom"):
    assert isinstance(obj_chave, ChaveNFCom), "Objeto deve ser do tipo ChaveNFCom"
    obj_chave.validar()
    chave_parcial = "%s%s%s%s%s%s%d%d%s" % (
        obj_chave.estado,
        obj_chave.emissao,
        obj_chave.cnpj,
        obj_chave.modelo,
        obj_chave.serie.zfill(3),
        str(obj_chave.numero).zfill(9),
        obj_chave.site_aut,
        obj_chave.tipo,
        obj_chave.codigo,
    )
    chave_parcial = re.sub("[^0-9]", "", chave_parcial)
    soma = sum(a*b for a, b in zip(reversed(chave_parcial), range(2, 9, 1)))
    dv = 11 - (soma%11)
    if suffix:
        return chave_parcial + dv + suffix
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