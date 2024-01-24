# -*- coding: utf-8 -*-
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import sys
from OpenSSL import crypto
from base64 import b64encode

from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken
from zeep.exceptions import Fault as ZeepFault
from requests.packages.urllib3 import disable_warnings

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura
from lxml import etree

import logging.config

class CustomTransport(Transport):  
    def post_xml(self, address, envelope, headers):  
        message = etree.tostring(envelope, encoding="unicode")  
        message = message.replace("&lt;", "<")  
        message = message.replace("&gt;", ">")  
        return self.post(address, message, headers)  

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    lote = ""
    referencia = ""
    kwargs["method"] = method
    if method == "RecepcionarLoteRps":
        referencia = kwargs.get("nfse").get("numero_lote")

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    if method == "RecepcionarLoteRps":
        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps:{0}{1}".format(
                item.get('numero'), item.get('serie'))

            signer.assina_xml(xml_send, reference)

        xml_signed_send = signer.assina_xml(
            xml_send, "lote:{0}".format(referencia))
    
        return xml_signed_send
    
    if method == "CancelarNfse":
        xml_signed_send = signer.assina_xml(xml_send, "1")
        return xml_signed_send

    return xml_string_send

def _send(certificado, method, **kwargs):
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'verbose': {
                'format': '%(name)s: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'zeep.transports': {
                'level': 'DEBUG',
                'propagate': True,
                'handlers': ['console'],
            },
        }
    })

    if not "base_url" in kwargs:
        #São Sebastião do passe - BA (default/ref)
        if kwargs["ambiente"] == "homologacao":
            base_url = "https://homologa-saosebastiaodopasse.saatri.com.br/Servicos/nfse.svc"
        else:
            base_url = "https://saosebastiaodopasse.saatri.com.br/Servicos/nfse.svc"
    else:
        base_url = kwargs["base_url"] + \
                    ("/" if kwargs["base_url"][len(kwargs["base_url"])-1] != "/" else "") + \
                    "servicos/nfse.svc"

    cert, key = extract_cert_and_key_from_pfx(
        certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    disable_warnings()
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    transport = CustomTransport(session=session)

    if method == "RecepcionarLoteRps":
        usuario = kwargs["nfse"]["lista_rps"][0]["usuario"]
        senha = kwargs["nfse"]["lista_rps"][0]["senha"]
    elif method == "ConsultarLoteRps":
        usuario = kwargs["consulta"]["usuario"]
        senha = kwargs["consulta"]["senha"]

    client = Client(wsdl=base_url + '?wsdl', transport=transport)

    xml_send = {}
    xml_send = {
        "nfseDadosMsg": "<![CDATA[" + kwargs["xml"] + "]]>",
        "nfseCabecMsg": """<![CDATA[<?xml version="1.0"?>
        <cabecalho xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.abrasf.org.br/nfse.xsd" versao="2.01">
            <versaoDados>2.01</versaoDados>
        </cabecalho>]]>""",
    }
    #No geral a Saatri não indica o service default
    service = client.bind('nfse', 'BasicHttpBinding_Infse')

    try:
        response = service[method](**xml_send)
        #response, obj = sanitize_response(response)
        obj = None
    except ZeepFault as e:
        response = e.__dict__
        obj = None
    except Exception as e:
        response = str(e)
        obj = None

    return {"sent_xml": xml_send, "received_xml": response, "object": obj}


def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRps", **kwargs)


def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRps", **kwargs)


def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRps", **kwargs)


def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)

    response = _send(certificado, "ConsultarLoteRps", **kwargs)
    xml = None

    try:
        xml_element = response['object'].find('.//Nfse')

        if sys.version_info[0] > 2:
            xml = str(etree.tostring(xml_element, encoding=str))
        else:
            xml = str(etree.tostring(xml_element, encoding="utf8"))
            
        xml = xml.replace('&#13;', '')
    except:
        pass

    return xml


def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "cancelarNfse", **kwargs)


def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "cancelarNfse", **kwargs)
