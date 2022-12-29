# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import signxml
from lxml import etree
from pytrustnfe.certificado import extract_cert_and_key_from_pfx
from signxml import XMLSigner
import sys

class Assinatura(object):

    NAMESPACE_SIG = 'http://www.w3.org/2000/09/xmldsig#'

    def __init__(self, cert, key):
        self.cert = cert
        self.key = key

    def assina_xml(self, xml):
        # busca tag que tem id(reference_uri), logo nao importa se tem namespace
        reference = xml.find(".//*[@Id]").attrib['Id']

        # retira acentos
        # xml_str = remover_acentos(etree.tostring(xml, encoding="unicode", pretty_print=False))
        # xml = etree.fromstring(xml_str)

        for element in xml.iter("*"):
            if element.text is not None and not element.text.strip():
                element.text = None

        signer = XMLSigner(
            method=signxml.methods.enveloped, signature_algorithm="rsa-sha1",
            digest_algorithm='sha1',
            c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')

        ns = {None: signer.namespaces['ds']}
        signer.namespaces = ns

        ref_uri = ('#%s' % reference) if reference else None
        signed_root = signer.sign(
            xml, key=self.key, cert=self.cert, reference_uri=ref_uri)

        ns = {'ns': self.NAMESPACE_SIG}
        # coloca o certificado na tag X509Data/X509Certificate
        tagX509Data = signed_root.find('.//ns:X509Data', namespaces=ns)
        etree.SubElement(tagX509Data, 'X509Certificate').text = self.cert
        
        encoding = 'utf8'
        if sys.version_info[0] > 2:
            encoding = str

        return etree.tostring(signed_root, encoding=encoding, pretty_print=False)
