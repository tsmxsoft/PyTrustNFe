# -*- coding: utf-8 -*-
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from requests import Session
from zeep import Client
from zeep.transports import Transport
from requests.packages.urllib3 import disable_warnings

from calendar import c
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    xml_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    return xml_send


def _send(certificado, method, **kwargs):
    base_url = kwargs.get("base_url", None)

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = Transport(session=session)

    client = Client(base_url, transport=transport)

    xml_send = kwargs["xml"]
    print('-----------------------')
    print('send')
    print(xml_send)
    if isinstance(xml_send, dict):
        return client.service[method](**xml_send)
    else:
        response = client.service[method](xml_send)
    print('response')
    print(response)
    response, obj = sanitize_response(response)
    print(response)
    return {"sent_xml": xml_send, "received_xml": response, "object": obj}


def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "EnviarLoteRpsEnvio", **kwargs)

def _abrirconexao(certificado, **kwargs):
    #Pega uma chave de conexão
    chave_acesso = _send(certificado, "autenticarContribuinte", xml={
        "identificacaoPrestador": kwargs["nfse"]["usuario"],
        "senha": kwargs["nfse"]["senha"],
    }, **kwargs)
    if not chave_acesso:
        raise Exception("Chave de acesso invalida, verifique as credenciais da prefeitura")
    return chave_acesso

def _fecharconexao(certificado, **kwargs):
    #Fecha conexão
    _ = _send(certificado, "finalizarSessao", xml={
        "hashIdentificador": kwargs["chave_acesso"],
    }, **kwargs)
    return True


def recepcionar_lote_rps(certificado, **kwargs):
    #Pega chave de acesso
    chave_acesso = _abrirconexao(certificado, **kwargs)
    #Gera o XML
    xml = xml_recepcionar_lote_rps(certificado, **kwargs)
    #Envia os dados 
    result_obj =  _send(certificado, "EnviarLoteRpsEnvio", xml={
        "identificacaoPrestador": kwargs["nfse"]["usuario"],
        "hashIdentificador": chave_acesso,
        "arquivo": xml,
    }, **kwargs)
    #Encerra conexão
    _fecharconexao(certificado, chave_acesso=chave_acesso, **kwargs)
    return {"sent_xml": xml, "received_xml": str(result_obj), "object": result_obj}

def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return None

def consultar_nfse_por_rps(certificado, **kwargs):
    return _send(certificado, "ConsultarNfseRpsEnvio", xml={
        "identificacaoRps": '{ano}{numero_rps}'.format(
            ano=kwargs["nfse"]["data_emissao"][:4],
            numero_rps=kwargs["nfse"]["rps"]["numero"].zfill(7),
        ),
        "identificacaoPrestador": kwargs["nfse"]["cnpj_prestador"],
    }, **kwargs)

def xml_consultar_lote_rps(certificado, **kwargs):
    return None

def consultar_lote_rps(certificado, **kwargs):
    return _send(certificado, "ConsultarLoteRpsEnvio", xml={
        "identificacaoPrestador": kwargs["consulta"]["cnpj_prestador"],
        "numeroProtocolo": kwargs["consulta"]["protocolo"],
    }, **kwargs)


def xml_cancelar_nfse(certificado, **kwargs):
    return None


def cancelar_nfse(certificado, **kwargs):
    return _send(certificado, "CancelarNfseMotivoEnvio", xml={
        "identificacaoPrestador": kwargs["nfse"]["usuario"],
        "senha": kwargs["nfse"]["senha"],
        "numeroNfse": kwargs["nfse"]["rps"]["numero"],
        "motivoCancelamento": kwargs["nfse"]["codigo_cancelamento"],
    }, **kwargs)
