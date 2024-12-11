# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.libre.assinatura import Assinatura
from lxml import etree
from zeep.transports import Transport
from requests import Session
import requests
from datetime import datetime, timedelta


def clean_x509(xml_string):
    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True, strip_cdata=False)
    root = etree.fromstring(xml_string, parser=parser)

    for elem in root.iter():
        if elem.tag.endswith('X509Certificate'):
            elem.text = elem.text[:len(elem.text)-1] if elem.text.endswith('\n') else elem.text
        if 'Id' in elem.attrib:
            del elem.attrib['Id']
    return etree.tostring(root, encoding='unicode')
    


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    referencia = ""
    if method == "RecepcionarLoteRpsSincrono" or method == "RecepcionarLoteRps":
        referencia = kwargs.get('nfse').get('numero_lote')

    xml_string_send = render_xml(path, "%s.xml" % method, True, False, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)
    

    if method in ["RecepcionarLoteRps",
                "RecepcionarLoteRpsSincrono"]:
        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps:{0}{1}".format(
                item.get('numero'), item.get('serie'))

            signer.assina_xml(xml_send, reference)

        xml_signed_send = signer.assina_xml(
            xml_send, "lote:{0}".format(referencia))
        

    elif method == "CancelarNfse":
        xml_signed_send = signer.assina_xml(xml_send, '{0}'.format(kwargs.get('nfse').get('numero')))
    
    else:
        print('--- xml ---')
        print(xml_string_send)
        return xml_string_send

    
    print('--- xml ---')
    print(xml_signed_send)
    return xml_signed_send


def xml_consultar_nfse_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfsePorRps", **kwargs)

def consultar_nfse_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
    xml = None


def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")

    base_url = None
    try:
        base_url = kwargs.get('base_url')
    except:
        raise Exception("É obrigatório informar a url")

    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, False, **{"soap_body":xml_send, "method": method })

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    action = "http://nfse.abrasf.org.br/%s" %(method)
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": action,
        "Operation": method,
        "Content-length": str(len(soap))
    }

    request = requests.post(base_url, data=soap, headers=headers)
    response, obj = sanitize_response(request.content.decode('utf8', 'ignore'))
    return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }



def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRps", **kwargs)

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return clean_x509(_render(certificado, "RecepcionarLoteRps", **kwargs))

def gerar_nfse(certificado, **kwargs):
    return _send(certificado, "GerarNfse", **kwargs)


def envio_lote_rps_sincrono(certificado, **kwargs):
    return _send(certificado, "RecepcionarLoteRpsSincrono", **kwargs)


def envio_lote_rps(certificado, **kwargs):
    return _send(certificado, "RecepcionarLoteRps", **kwargs)


def xml_cancelar_nfse(certificado, **kwargs):
    return clean_x509(_render(certificado, "CancelarNfse", **kwargs))


def cancelar_nfse(certificado, **kwargs):
    if 'xml' not in kwargs:
        kwargs['xml'] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "CancelarNfse", **kwargs)


def substituir_nfse(certificado, **kwargs):
    return _send(certificado, "SubstituirNfse", **kwargs)


def consulta_situacao_lote_rps(certificado, **kwargs):
    return _send(certificado, "ConsultaSituacaoLoteRPS", **kwargs)


def consulta_nfse_por_rps(certificado, **kwargs):
    return _send(certificado, "ConsultarNfsePorRps", **kwargs)

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, "ConsultarLoteRps", **kwargs)


def consulta_nfse_servico_prestado(certificado, **kwargs):
    return _send(certificado, "ConsultarNfseServicoPrestado", **kwargs)


def consultar_nfse_servico_tomado(certificado, **kwargs):
    return _send(certificado, "ConsultarNfseServicoTomado", **kwargs)


def consulta_nfse_faixe(certificado, **kwargs):
    return _send(certificado, "ConsultarNfseFaixa", **kwargs)


def consulta_cnpj(certificado, **kwargs):
    return _send(certificado, "ConsultaCNPJ", **kwargs)