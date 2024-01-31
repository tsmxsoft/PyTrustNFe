# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import os
import sys
import requests
from lxml import etree
from .patch import has_patch
from .assinatura import Assinatura
from pytrustnfe.xml import render_xml, sanitize_response
from pytrustnfe.utils import gerar_chave_nfsenacional, gerar_chave_nfsenacional_dps, ChaveNFSeNacional, ChaveNFSeNacionalDPS
from pytrustnfe.Servidores import localizar_url
from pytrustnfe.certificado import extract_cert_and_key_from_pfx, save_cert_key
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Zeep
from requests import Session
from zeep import Client
from zeep.transports import Transport

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
        "ibge_num": kwargs["NFSe"]["infNFSe"]["cLocEmi"],
        "ambiente": kwargs["NFSe"]["infNFSe"]["ambGer"],
        "tipo_insc_fed": 1 if len(kwargs["NFSe"]["infNFSe"]["emit"]["cnpj_cpf"]) == 11 else 2,
        "insc_fed": kwargs["NFSe"]["infNFSe"]["emit"]["cnpj_cpf"],
        "numero": kwargs["NFSe"]["infNFSe"]["nNFSe"],
        "dt_emissao": "%s%s"
        % (
            kwargs["NFSe"]["infNFSe"]["DPS"]["infDPS"]["dhEmi"][2:4],
            kwargs["NFSe"]["infNFSe"]["DPS"]["infDPS"]["dhEmi"][5:7],
        ),
        "codigo": kwargs["NFSe"]["infNFSe"]["ide"]["cNF"],
    }
    chave_nfse = ChaveNFSeNacional(**vals)
    chave_nfse = gerar_chave_nfsenacional(chave_nfse, "NFS")
    kwargs["NFSe"]["infNFSe"]["Id"] = chave_nfse


def _generate_nfse_dps_id(**kwargs):
    dps = kwargs["NFSe"]["infNFSe"]["DPS"]
    vals = {
        "ibge_num": dps["cLocEmi"],
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
    xmlElem_send = render_xml(path, "%s_%s.xml" % (method, VERSAO), True, **kwargs)

    if sign:
        signer = Assinatura(certificado.pfx, certificado.password)
        if method == "NFSe":
            #Assina DPS
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

    if method == "NFSe":
        payload = {
            "dpsXmlGZipB64": xml_send,
        }
    request = requests.post(base_url,data=payload,verify=False,cert=(cert, key))
    return {"sent_xml": xml_send, "received": request, "obj": None}



def xml_autorizar_nfse(certificado, **kwargs):
    _generate_nfse_id(**kwargs)
    _generate_nfse_dps_id(**kwargs) #Um dia vai ser 1-N, certeza.
    return _render(certificado, "NFSe", True, **kwargs)


def autorizar_nfse(certificado, **kwargs):  # Assinar
    kwargs["b64encode"] = True
    if "xml" not in kwargs:
        kwargs["xml"] = xml_autorizar_nfse(certificado, **kwargs)
    kwargs["base_url"] = "https://sefin.nfse.gov.br/sefinnacional/nfse"
    return _send(certificado, "NFSe", **kwargs)

def consultar_nfse(certificado, **kwargs):
    