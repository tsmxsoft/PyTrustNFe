# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# Endereços Simpliss Piracicaba
# Homologação: http://wshomologacao.simplissweb.com.br/nfseservice.svc
# Homologação site: http://homologacaonovo.simplissweb.com.br/Account/Login

# Prod:http://sistemas.pmp.sp.gov.br/semfi/simpliss/contrib/Account/Login
# Prod:http://sistemas.pmp.sp.gov.br/semfi/simpliss/ws_nfse/nfseservice.svc

import os
from lxml import etree

from requests import Session
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.tecnos.assinatura import Assinatura

from datetime import datetime
from requests import Session
from zeep import Client
from zeep.transports import Transport

estados = {
    'AC': 1,'AL': 2,'AM': 4,
    'AP': 3,'BA': 5,'CE': 6,
    'DF': 7,'ES': 8,'GO': 9,
    'MA': 10,'MG': 13,'MS': 12,
    'MT': 11,'PA': 14,'PB': 15,
    'PE': 17,'PI': 18,'PR': 16,
    'RJ': 19,'RN': 20,'RO': 22,
    'RR': 23,'RS': 21,'SC': 24,
    'SE': 26,'SP': 25,'TO': 27,
}

class TransportPlugin:
    def egress(self, envelope, http_headers, operation, binding_options):
        xml_string = etree.tostring(envelope)
        xml_string = xml_string.replace("&lt;", "<")
        xml_string = xml_string.replace("&gt;", ">")
        xml_string = xml_string.replace("&amp;", "&")
        parser = etree.XMLParser(strip_cdata=False)
        new_envelope = etree.XML(xml_string, parser=parser)
        return new_envelope, http_headers

def _render_xml(certificado, method, **kwargs):
    kwargs['method'] = method

    #Numero do lote formatado - Tecnos
    #<!--1 - identificação de envio de lote sincrono-->
    #<!--0000 - ano do lote enviado no formato AAAA-->
    #<!--00000000000009 - numero do CPF/CNPJ do contribuinte formatado com 14 posições-->
    #<!--0000000000000009 - número sequencial do lote formatado com 16 posições-->
    kwargs['nfse']['numero_lote_formatado'] = "1%s%s%s" %(
        str(datetime.now().year),
        str(kwargs['nfse']['cnpj_prestador']).zfill(14),
        str(kwargs['nfse']['numero_lote']).zfill(16)
    )
    #Numero de cada RPS formatado - Tecnos
    #<!--1 - Tipo de operação, no caso envio-->
    #<!--91593376000102 - Documento do prestador formatado com 14 posições-->
    #<!--0000000000000007 - Número do RPS formatado com 16 posições-->
    for item in kwargs["nfse"]["lista_rps"]:
        item["numero_rps_formatado"] = "1%s%s" %(
            str(kwargs['nfse']['cnpj_prestador']).zfill(14),
            str(item["numero"]).zfill(16)
        )
        item["tomador"]["uf_codigo"] = estados[item["tomador"]["uf"]]
        if "intermediario" in item:
            item["intermediario"]["uf_codigo"] = estados[item["tomador"]["uf"]]


    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=False, remove_comments=False, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)
    xml_string_send = render_xml(path, "%s.xml" % method, False, **kwargs)
    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    if method == "EnviarLoteRpsSincrono":
        for item in kwargs["nfse"]["lista_rps"]:
            xml_signed_send = signer.assina_xml(xml_send, item["numero_rps_formatado"],parser=parser)
    
    return xml_signed_send

def _send(certificado, method, **kwargs):
    base_url = "%s:%s/%s.asmx?wsdl" %(kwargs["base_url"],str(kwargs["ws_port"]),kwargs["soap_action"])


    xml_send = "<![CDATA[" + kwargs["xml"] + "]]>"
    xml_cabecalho = """<![CDATA[<cabecalho xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" versao="20.01" xmlns="http://www.nfse-tecnos.com.br/nfse.xsd"><versaoDados>20.01</versaoDados></cabecalho>]]>""".decode('utf-8')
    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    client = Client(wsdl=base_url, transport=transport, plugins=[TransportPlugin()])
    client.set_ns_prefix(None, "http://tempuri.org/m"+kwargs["soap_action"])

    response = client.service["m"+kwargs["soap_action"]](xml_send,xml_cabecalho)
    response, obj = sanitize_response(response)

    return {"sent_xml": str(xml_send), "received_xml": str(response), "object": obj}


def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render_xml(certificado, "EnviarLoteRpsSincrono", **kwargs)


def recepcionar_lote_rps(certificado, **kwargs):
    kwargs["ws_port"] = 9091
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
        kwargs["soap_action"] = "EnvioLoteRPSSincrono"
    return _send(certificado,"EnviarLoteRpsSincrono", **kwargs)


def xml_consultar_situacao_lote(certificado, **kwargs):
    return _render_xml(certificado, "ConsultarSituacaoLoteRps", **kwargs)


def consultar_situacao_lote(certificado, **kwargs):
    kwargs["ws_port"] = 9097
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_situacao_lote(certificado, **kwargs)
    return _send(None, "ConsultarSituacaoLoteRps", **kwargs)


def consultar_nfse_por_rps(certificado, **kwargs):
    kwargs["ws_port"] = 9095
    return _send(None, "ConsultarNfsePorRps", **kwargs)


def xml_consultar_lote_rps(certificado, **kwargs):
    return _render_xml(certificado, "ConsultarLoteRps", **kwargs)


def consultar_lote_rps(certificado, **kwargs):
    kwargs["ws_port"] = 9097
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, "ConsultarLoteRps", **kwargs)


def xml_consultar_nfse(certificado, **kwargs):
    return _render_xml(certificado, "ConsultarNfse", **kwargs)


def consultar_nfse(certificado, **kwargs):
    kwargs["ws_port"] = 9083
    return _send("ConsultarNfse", **kwargs)


def xml_cancelar_nfse(certificado, **kwargs):
    return _render_xml(certificado, "CancelarNfse", **kwargs)


def cancelar_nfse(certificado, **kwargs):
    kwargs["ws_port"] = 9098
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send("CancelarNfse", **kwargs)


def xml_gerar_nfse(certificado, **kwargs):
    return _render_xml(certificado, "GerarNfse", **kwargs)


def gerar_nfse(certificado, **kwargs):
    kwargs["ws_port"] = 9092
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send("GerarNfse", **kwargs)
