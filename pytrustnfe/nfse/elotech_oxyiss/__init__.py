# -*- coding: utf-8 -*-
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from OpenSSL import crypto
from base64 import b64encode

from requests import Session
from zeep import Client
from zeep.transports import Transport
from requests.packages.urllib3 import disable_warnings

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura

from lxml import etree
import requests

from collections import defaultdict


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(remove_blank_text=True, 
                             remove_comments=True, 
                             strip_cdata=False)

#    signer = Assinatura(certificado.pfx, certificado.password)
    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)
    xml_send = etree.fromstring(xml_string_send, parser=parser)
#    referencia = ""

#    if method in ["RecepcionarLoteRps", "RecepcionarLoteRpsSincrono"]:
#        referencia = kwargs.get("nfse").get("numero_lote")
#        for item in kwargs["nfse"]["lista_rps"]:
#            reference = "rps:{0}{1}".format(
#                item.get('numero'), item.get('serie'))
#            
#            signer.assina_xml(xml_send, reference)

#        xml_signed_send = signer.assina_xml(
#            xml_send, "lote:{0}".format(referencia))
#    else:
#        xml_signed_send = etree.tostring(xml_send)
    xml_signed_send = etree.tostring(xml_send)

    return xml_signed_send

def _send(certificado, method, **kwargs):
    base_url = kwargs.get('base_url',None)
    if not base_url:
        raise Exception("Url do serviço não definido")
    
    xml_send = kwargs["xml"]
    print(xml_send)
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, **{"soap_body":xml_send, "method": method })

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    session = Session()
    session.cert = (cert, key)
    session.verify = False
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "Content-length": str(len(soap))
    }
    print(base_url)

    request = requests.post(base_url, data=soap, headers=headers)
    response, obj = sanitize_response(request.content)
    print(response)
    return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }

def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRpsSincrono", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRpsSincrono", **kwargs)

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, "ConsultarLoteRps", **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "cancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "cancelarNfse", **kwargs)
