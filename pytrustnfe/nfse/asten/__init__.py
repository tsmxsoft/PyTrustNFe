# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import os
import sys
import requests

from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfse.asten.assinatura import Assinatura
from zeep.transports import Transport
from requests import Session
from lxml import etree


def clean_x509(xml_string):
    if isinstance(xml_string, str):
        parser = etree.XMLParser(remove_blank_text=True, remove_comments=True, strip_cdata=False)
        root = etree.fromstring(xml_string, parser=parser)

        for elem in root.iter():
            if elem.tag.endswith('X509Certificate'):
                if '\n' in elem.text:
                    elem.text = elem.text.replace('\n', '')
        return etree.tostring(root, encoding='unicode')
    
    return xml_string


def _render(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    xml_string_send = render_xml(path, "%s.xml" % method, True, **kwargs)

    # xml object
    xml_send = etree.fromstring(
        xml_string_send, parser=parser)

    if method == "RecepcionarLoteRps" \
        or method == "RecepcionarLoteRpsSincrono":
        referencia = kwargs.get("nfse").get("numero_lote")

        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps:{0}{1}".format(
                item.get('numero'), item.get('serie'))
            
            signer.assina_xml(xml_send, reference)
            
        xml_signed_send = signer.assina_xml(
            xml_send, "lote:{0}".format(referencia))
        
        
    elif method == "CancelarNfse":
        xml_signed_send = signer.assina_xml(xml_send,"rps:%s" %str(kwargs["nfse"]["rps"]["numero"]))
    
    else:
        xml_signed_send = etree.tostring(xml_send)

    return xml_signed_send

def _send(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")    

    if kwargs["ambiente"] == "homologacao":
        url = "https://wshomo.pelotas.rs.gov.br/wsnfse/NfseWSISAPI.dll/soap/INfse?wsdl"
    else:
        url = "https://ws.pelotas.rs.gov.br/wsnfse/NfseWSISAPI.dll/soap/INfse?wsdl"

    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, False, soap_body=xml_send, method=method)

    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)
    session = Session()
    session.cert = (cert, key)
    session.verify = False

    action = "http://nfse.abrasf.org.br/%s" %(method)
    headers = {
        "SOAPAction": action,
        "Content-length": str(len(soap)),
        'Content-Type': 'text/xml; charset=utf-8'
    }

    request = requests.post(url, data=soap, cert=(cert, key), headers=headers)
    response, obj = sanitize_response(request.content)
    return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }



def xml_recepcionar_lote_rps(certificado, **kwargs):
    return clean_x509(_render(certificado, "RecepcionarLoteRps", **kwargs))


def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
        print(kwargs["xml"])
    return clean_x509(_send(certificado, "RecepcionarLoteRps", **kwargs))


def xml_recepcionar_lote_rps_sincrono(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRpsSincrono", **kwargs)


def recepcionar_lote_rps_sincrono(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    if len(kwargs["xml"]["nfse"]["lista_rps"]) > 2:
        return {}
    return _send(certificado, "RecepcionarLoteRpsSincrono", **kwargs)


def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarNfsePorRps", **kwargs)

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = _render(certificado, "ConsultarNfsePorRps", **kwargs)
    return _send(certificado, "ConsultarNfsePorRps", **kwargs)


def xml_cancelar_nfse(certificado, **kwargs):
    return clean_x509(_render(certificado, "CancelarNfse", **kwargs))

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    return  _send(certificado, "CancelarNfse", **kwargs)


def xml_consultar_lote_rps(certificado, **kwargs):
    return _render(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    return _send(certificado, "ConsultarLoteRps", **kwargs)


def substituir_nfse(certificado, **kwargs):
    return _send(certificado, "SubstituirNfse", **kwargs)