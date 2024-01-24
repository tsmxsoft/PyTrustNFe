# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# Endereços Simpliss Piracicaba
# Homologação: http://wshomologacao.simplissweb.com.br/nfseservice.svc
# Homologação site: http://homologacaonovo.simplissweb.com.br/Account/Login

# Prod:http://sistemas.pmp.sp.gov.br/semfi/simpliss/contrib/Account/Login
# Prod:http://sistemas.pmp.sp.gov.br/semfi/simpliss/ws_nfse/nfseservice.svc

import os
import io
from lxml import etree
from requests import Session
from zeep.transports import Transport
from pytrustnfe.xml import render_xml, sanitize_response

from zeep import Client, Settings, xsd
from datetime import datetime, timedelta
from pytrustnfe.nfe.assinatura import Assinatura
from pytrustnfe.nfse.ipm.utils_tom import ibge_to_tom
import requests 

def _render_xml(certificado, method, **kwargs):
    kwargs['method'] = method

    if method == "nfse":
        kwargs["nfse"]["cidade_tom"] = ibge_to_tom(str(kwargs["nfse"]["servico"]["codigo_municipio"]))

    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)
    
    if method == "nfse":
        xml_signed_send = signer.assina_xml(
            xml_send, "rps:{0}{1}".format(
                kwargs["nfse"]["numero"],
                kwargs["nfse"]["serie"],
            ),sign_namespace=True)
        return xml_signed_send

    return etree.tostring(xml_send)

def _send(certificado, method, **kwargs):
    if "base_url" in kwargs:
        base_url = kwargs.get('base_url') + \
                ("/" if kwargs["base_url"][len(kwargs["base_url"])-1] != "/" else "") + \
                "datacenter/include/nfw/importa_nfw/nfw_import_upload.php"
    else:
        base_url = "http://sync.nfs-e.net/datacenter/include/nfw/importa_nfw/nfw_import_upload.php"

    data = {
        "login": kwargs.get("nfse").get("lista_rps")[0].get("usuario"),
        "senha": kwargs.get("nfse").get("lista_rps")[0].get("senha"),
        "cidade": kwargs.get("nfse").get("lista_rps")[0].get("cidade_tom"),
    }
    outfile = io.BytesIO(kwargs.get('xml'))
    files = {
        'f1': ('%s_%s_%s.xml' %( \
            kwargs.get("nfse").get("lista_rps")[0].get("prestador").get("cnpj"), \
            datetime.now().strftime("%y%m"),
            datetime.now().strftime("%H%M%S") \
            ), outfile.getvalue(), 'text/xml')
    }
    headers = {
    }
    response = requests.post(base_url + "?eletron=1", files=files, data=data, headers=headers)

    return {"sent_xml": kwargs.get("xml"), "received_xml": response.text, "object": "" }

def xml_gerar_nfse(certificado, **kwargs):
    return _render_xml(certificado, "nfse", **kwargs)


def gerar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_gerar_nfse(certificado, **kwargs)
    return _send(certificado, "nfse", **kwargs)


def xml_recepcionar_lote_rps(certificado, **kwargs):
    lote_nfse = []
    for nfse in kwargs.get("nfse").get("lista_rps"):
        kwargs['nfse'] = nfse
        lote_nfse.append(xml_gerar_nfse(certificado, **kwargs))
    return lote_nfse


def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    if isinstance(kwargs["xml"], list):
        obj = ''
        for i, nfse in enumerate(kwargs["xml"]):
            kwargs["xml"] = nfse
            tmp = gerar_nfse(certificado, **kwargs)
            obj += str(tmp)
        return obj
    return _send(certificado, "nfse", **kwargs)


def xml_consultar_situacao_lote(certificado, **kwargs):
    return _render_xml(certificado, "ConsultarSituacaoLoteRps", **kwargs)


def consultar_situacao_lote(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_situacao_lote(certificado, **kwargs)
    return _send(None, "ConsultarSituacaoLoteRps", **kwargs)


def consultar_nfse_por_rps(certificado, **kwargs):
    return _send(None, "ConsultarNfsePorRps", **kwargs)


def consultar_lote_rps(certificado, **kwargs):
    return _send(certificado, "consultarLoteRPS", **kwargs)


def xml_consultar_nfse(certificado, **kwargs):
    return _render_xml(certificado, "ConsultarNfse", **kwargs)


def consultar_nfse(certificado, **kwargs):
    return _send("ConsultarNfse", **kwargs)


def cancelar_nfse(certificado, **kwargs):
    return _send(certificado, "cancelarNFSE", **kwargs)