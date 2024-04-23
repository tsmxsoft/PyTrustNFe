# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

#Homologação: https://www.producaorestrita.nfse.gov.br/swagger/contribuintesissqn/#/
#Produção: https://www.nfse.gov.br/swagger/contribuintesissqn/#/

import os
import sys
import certifi
import requests
from lxml import etree
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.utils import gerar_chave_nfsenacional, gerar_chave_nfsenacional_dps, ChaveNFSeNacional, ChaveNFSeNacionalDPS
from pytrustnfe.Servidores import localizar_url
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from pytrustnfe.nfsenacional.assinatura import Assinatura
#B64 + Gzip
import gzip
import base64
try:
    from StringIO import StringIO
except ImportError:
    import io as StringIO

VERSAO = "1.00"

def _generate_nfse_id(**kwargs):
    vals = {
        "ibge_mun": kwargs["NFSe"]["infNFSe"]["cLocEmi"],
        "ambiente": kwargs["NFSe"]["infNFSe"]["ambGer"],
        "tipo_insc_fed": 1 if len(kwargs["NFSe"]["infNFSe"]["emit"]["cnpj_cpf"]) == 11 else 2,
        "insc_fed": kwargs["NFSe"]["infNFSe"]["emit"]["cnpj_cpf"],
        "numero": kwargs["NFSe"]["infNFSe"]["nNFSe"],
        "dt_emissao": "%s%s"
        % (
            kwargs["NFSe"]["infNFSe"]["DPS"]["infDPS"]["dhEmi"][2:4],
            kwargs["NFSe"]["infNFSe"]["DPS"]["infDPS"]["dhEmi"][5:7],
        ),
        "codigo": kwargs["NFSe"]["infNFSe"]["cNFSe"],
    }
    chave_nfse = ChaveNFSeNacional(**vals)
    chave_nfse = gerar_chave_nfsenacional(chave_nfse, "NFS")
    kwargs["NFSe"]["infNFSe"]["Id"] = chave_nfse


def _generate_nfse_dps_id(**kwargs):
    dps = kwargs["NFSe"]["infNFSe"]["DPS"]["infDPS"]
    vals = {
        "ibge_mun": dps["cLocEmi"],
        "tipo_insc_fed": 1 if len(dps["prest"]["cnpj_cpf"]) == 11 else 2,
        "insc_fed": dps["prest"]["cnpj_cpf"],
        "serie": dps["serie"],
        "numero": dps["nDPS"],
    }
    chave_nfse_dps = ChaveNFSeNacionalDPS(**vals)
    chave_nfse_dps = gerar_chave_nfsenacional_dps(chave_nfse_dps, "DPS")
    kwargs["NFSe"]["infNFSe"]["DPS"]["Id"] = chave_nfse_dps


def _render(certificado, method, sign, **kwargs):
    path = os.path.join(os.path.dirname(__file__), "templates")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    signer = Assinatura(certificado.pfx, certificado.password)
    xml_string_send = render_xml(path, "%s_%s.xml" % (method, VERSAO), True, **kwargs)
    
    xmlElem_send = etree.fromstring(
        xml_string_send, parser=parser)

    if sign:
        signer = Assinatura(certificado.pfx, certificado.password)
        if method == "NFSe":
            #Assina DPS (hoje 1-1, talvez amanhã 1-N)
            signer.assina_xml(xmlElem_send, kwargs["NFSe"]["infNFSe"]["DPS"]["Id"])
            #Assina NFSe
            xml_send = signer.assina_xml(xmlElem_send, kwargs["NFSe"]["infNFSe"]["Id"])

    else:
        if sys.version_info[0] > 2:
            xml_send = etree.tostring(xmlElem_send, encoding=str)
        else:
            xml_send = etree.tostring(xmlElem_send, encoding="utf8")

    if kwargs.get("b64encode"):
        out_file = StringIO()
        gzip_file = gzip.GzipFile(fileobj=out_file, mode='wb')
        gzip_file.write(xml_send.encode('utf-8'))
        gzip_file.close()
        b64_bytes = base64.b64encode(out_file.getvalue())
        xml_send = b64_bytes.decode('utf-8')

    return xml_send


def _send(certificado, method, **kwargs):
    xml_send = kwargs["xml"]
    base_url = kwargs["base_url"]
    cert, key = extract_cert_and_key_from_pfx(certificado.pfx, certificado.password)
    cert, key = save_cert_key(cert, key)

    headers = {
        "Content-Type": "application/json",
    }
    params = {}
    payload = {}
    if method == "NFSe":
        payload = {
            "dpsXmlGZipB64": xml_send,
        }
    request = requests.post(base_url,json=payload, params=params, cert=(cert, key), headers=headers, verify=certifi.where())
    print("Status: %d" % request.status_code)
    return {"sent_xml": xml_send, "received": request.json(), "obj": None}



def xml_autorizar_nfse(certificado, **kwargs):
    _generate_nfse_id(**kwargs)
    _generate_nfse_dps_id(**kwargs) #Um dia vai ser 1-N, certeza.
    return _render(certificado, "NFSe", True, **kwargs)


def autorizar_nfse(certificado, **kwargs):  # Assinar
    kwargs["b64encode"] = True
    if "xml" not in kwargs:
        kwargs["xml"] = xml_autorizar_nfse(certificado, **kwargs)
    kwargs["base_url"] = "https://sefin.nfse.gov.br/sefinnacional/nfse"
    if "ambiente" in kwargs:
        if kwargs["ambiente"] == "homologacao":
            kwargs["base_url"] = "https://sefin.producaorestrita.nfse.gov.br/SefinNacional/nfse"
    return _send(certificado, "NFSe", **kwargs)
