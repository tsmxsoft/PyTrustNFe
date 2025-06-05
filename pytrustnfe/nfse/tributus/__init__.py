# -*- coding: utf-8 -*-
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from OpenSSL import crypto
from base64 import b64encode

import requests
from requests.packages.urllib3 import disable_warnings

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura
from lxml import etree
import sys

def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    referencia = ""
    if method == "RecepcionarLoteRpsSincrono" or method == "RecepcionarLoteRps":
        referencia = kwargs.get("nfse").get("numero_lote")

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    if method == "RecepcionarLoteRpsSincrono" or method == "RecepcionarLoteRps":
        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps:{0}{1}".format(
                item.get('numero'), item.get('serie'))

            xml_signed_send = signer.assina_xml(xml_send, reference)

        xml_signed_send = signer.assina_xml(
            xml_send, "lote:{0}".format(referencia))
    elif method == "CancelarNfse":
        xml_signed_send = signer.assina_xml(
            xml_send, "1")
    else:
        xml_signed_send = etree.tostring(xml_send)

    print ('--- xml ---')
    print (xml_signed_send)

    return xml_signed_send


def _send(certificado, method, **kwargs):
    base_url = ""
    if kwargs["ambiente"] == "homologacao":
        base_url = "https://www.tributosmunicipais.com.br/nfse/api/"
    else:
        base_url = "https://www.tributosmunicipais.com.br/nfse/api/"

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, **{"soap_body":xml_send, "method": method})

    disable_warnings()
    session = requests.Session()
    session.cert = (cert, key)
    session.verify = False
    
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": base_url + method,
        "Operation": method,
        "Content-length": str(len(soap))
    }

    token = kwargs.get('nfse', {}).get('chave_digital', '')
    if token:
        base_url += '?tokenAuth=%s' % token

    request = requests.post(base_url, data=soap, headers=headers)
    try:
        response, obj = sanitize_response(request.content)
    except Exception as e:
        return {"sent_xml": str(soap), "received_xml": str(e), "object": None}

    return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }
    

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
    return _send(certificado, "ConsultarLoteRps", **kwargs)

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return _send(certificado, "CancelarNfse", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)

    print (kwargs["xml"])
    
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
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


def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfsePorRps", **kwargs)