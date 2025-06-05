# -*- coding: utf-8 -*-
# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import sys
import requests
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.certificado import extract_cert_key_and_ca_from_pfx, save_cert_key
from pytrustnfe.nfe.assinatura import Assinatura
from lxml import etree
if sys.version_info[0] > 2:
    from html.parser import HTMLParser
else:
    from HTMLParser import HTMLParser



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

    if method in ["RecepcionarLoteRps",
                  "RecepcionarLoteRpsSincrono"]:
        for item in kwargs["nfse"]["lista_rps"]:
            reference = "rps:{0}{1}".format(
                item.get('numero'), item.get('serie',''))

            signer.assina_xml(xml_send, reference)

        xml_signed_send = signer.assina_xml(
            xml_send, "lote:{0}".format(referencia))
    elif method == "CancelarNfse":
        xml_signed_send = signer.assina_xml(xml_send, "rps:{0}".format(kwargs.get("nfse").get("rps").get("numero")))
    else:
        print ('--- xml ---')
        print (xml_string_send)
        return xml_string_send

    print ('--- xml ---')
    print (xml_signed_send)
    return xml_signed_send

def _render_unsigned(certificado, method, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(remove_blank_text=True, 
                             remove_comments=True, 
                             strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)

    xml = render_xml(path, "%s.xml" % method, True, **kwargs)

    return xml

def _send(certificado, method, **kwargs):
    base_url = ""
    if kwargs["ambiente"] == "homologacao":
        base_url = kwargs.get("base_url") or "https://wsnfse.vitoria.es.gov.br/homologacao/NotaFiscalService.asmx"
    else:
        base_url = kwargs.get("base_url") or "https://wsnfse.vitoria.es.gov.br/producao/NotaFiscalService.asmx"

    xml_send = kwargs["xml"]
    path = os.path.join(os.path.dirname(__file__), "templates")
    soap = render_xml(path, "SoapRequest.xml", False, **{"soap_body":xml_send, "method": method })

    action = 'http://www.abrasf.org.br/nfse.xsd/%s' %(method)
    headers = {
        'SoapAction': action,
        'Content-Type': 'text/xml;charset=UTF-8'
    }
    with extract_cert_key_and_ca_from_pfx(certificado.pfx, certificado.password) as cert:
        request = requests.post(base_url, data=soap, headers=headers, cert=cert)
        try:
            response, obj = sanitize_response(request.content.decode('utf8', 'ignore'))
            try:
                return {"sent_xml": str(soap), "received_xml": str(response.encode('utf8')), "object": obj.Body }
            except:
                return {"sent_xml": str(soap), "received_xml": str(response), "object": obj.Body }
        except:
            try:
                return {"sent_xml": str(soap), "received_xml": str(request.content.decode('utf8', 'ignore')), "object": None }
            except:
                return {"sent_xml": str(soap), "received_xml": str(request.content), "object": None }


def xml_recepcionar_lote_rps(certificado, **kwargs):
    return _render(certificado, "RecepcionarLoteRps", **kwargs)

def recepcionar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_recepcionar_lote_rps(certificado, **kwargs)
    return _send(certificado, "RecepcionarLoteRps", **kwargs)

def xml_consultar_lote_rps(certificado, **kwargs):
    return _render_unsigned(certificado, "ConsultarLoteRps", **kwargs)

def consultar_lote_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_lote_rps(certificado, **kwargs)
    response = _send(certificado, "ConsultarLoteRps", **kwargs)
    xml = None

    try:
        xml_element = response['object'].find('.//ConsultarLoteRpsResult')

        if sys.version_info[0] > 2:
            xml = str(etree.tostring(xml_element, encoding=str))
        else:
            xml = str(etree.tostring(xml_element, encoding="utf8"))
        #unescape
        xml = HTMLParser().unescape(xml)
    except:
        pass

    return xml

def xml_cancelar_nfse(certificado, **kwargs):
    return _render(certificado, "CancelarNfse", **kwargs)

def cancelar_nfse(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_cancelar_nfse(certificado, **kwargs)
    response = _send(certificado, "CancelarNfse", **kwargs)
    xml = None

    try:
        xml_element = response['object'].find('.//CancelarNfseResult')

        if sys.version_info[0] > 2:
            xml = str(etree.tostring(xml_element, encoding=str))
        else:
            xml = str(etree.tostring(xml_element, encoding="utf8"))
        #unescape
        xml = HTMLParser().unescape(xml)
    except:
        pass

    return xml

def consultar_nfse_por_rps(certificado, **kwargs):
    if "xml" not in kwargs:
        kwargs["xml"] = xml_consultar_nfse_por_rps(certificado, **kwargs)

    print (kwargs["xml"])
    
    response = _send(certificado, "ConsultarNfsePorRps", **kwargs)
    print(response['received_xml'])
    xml = None

    try:
        xml_element = response['object'].find('.//ConsultarNfsePorRpsResult')

        if sys.version_info[0] > 2:
            xml = str(etree.tostring(xml_element, encoding=str))
        else:
            xml = str(etree.tostring(xml_element, encoding="utf8"))
        #unescape
        xml = HTMLParser().unescape(xml)
    except:
        pass

    return xml


def xml_consultar_nfse_por_rps(certificado, **kwargs):
    return _render_unsigned(certificado, "ConsultarNfsePorRps", **kwargs)