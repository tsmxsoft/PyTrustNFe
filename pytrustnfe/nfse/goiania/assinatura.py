# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from signxml import XMLSigner, methods
from pytrustnfe.nfe.assinatura import Assinatura as _Assinatura
from OpenSSL import crypto

class Assinatura(_Assinatura):

    def __init__(self, cert, key):
        self.cert = cert
        self.key = key

    def extract_cert_key(self):
        pfx = crypto.load_pkcs12(self.cert, self.key)
        key = crypto.dump_privatekey(crypto.FILETYPE_PEM, pfx.get_privatekey())
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, pfx.get_certificate())

        return cert, key

    def assina_xml(self, xml_element):
        cert, key = self.extract_cert_key()

        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm=u"rsa-sha1",
            digest_algorithm=u"sha1",
            c14n_algorithm=u"http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        )

        ns = {}
        ns[None] = signer.namespaces["ds"]
        signer.namespaces = ns
        element_signed = xml_element.find(".//{http://nfse.goiania.go.gov.br/xsd/nfse_gyn_v02.xsd}Rps")
        signed_root = signer.sign(
            xml_element, key=key.encode(), cert=cert.encode()
        )
        signature = signed_root.find(
            ".//{http://www.w3.org/2000/09/xmldsig#}Signature"
        )

        if element_signed is not None and signature is not None:
            parent = xml_element.getchildren()[0]
            parent.append(signature)

        return etree.tostring(xml_element, encoding="utf-8")