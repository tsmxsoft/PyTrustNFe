# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from OpenSSL import crypto
import signxml
from lxml import etree
from pytrustnfe.nfe.assinatura import XMLSigner
import sys

class Assinatura(object):

    def __init__(self, cert, key):
        self.cert = cert
        self.key = key

    def extract_cert_key(self):
        pfx = crypto.load_pkcs12(self.cert, self.key)
        key = crypto.dump_privatekey(crypto.FILETYPE_PEM, pfx.get_privatekey())
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, pfx.get_certificate())

        return cert, key

    def assina_xml(self, xml_element, reference, getchildren=False, **kwargs):
        cert, key = self.extract_cert_key()

        signer = XMLSigner(method=signxml.methods.enveloped, 
                           signature_algorithm="rsa-sha1",
                           digest_algorithm='sha1',
                           c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')

        ns = {}
        ns[None] = signer.namespaces['ds']
        signer.namespaces = ns

        ref_uri = ('#%s' % reference) if reference else None

        element = xml_element.find(".//*[@id='%s']" % (reference))
        if element is None:
            element = xml_element.find(".//*[@Id='%s']" % (reference))

        signed_root = signer.sign(
            element, key=key, cert=cert,
            reference_uri=ref_uri)

        if reference:
            element_signed = xml_element.find(".//*[@id='%s']" % (reference))
            if element_signed is None:
                element_signed = xml_element.find(".//*[@Id='%s']" % (reference))
            signature = signed_root.findall(".//{http://www.w3.org/2000/09/xmldsig#}Signature")[-1]

            if kwargs.get('include_ref'):
                signature.set(kwargs['include_ref'], reference)

            if element_signed is not None and signature is not None:
                parent = element_signed.getparent()
                parent.append(signature)

            if kwargs.get('remove_attrib'):
                element_signed.attrib.pop(kwargs['remove_attrib'], None)

        if sys.version_info[0] > 2:
            return etree.tostring(xml_element, encoding=str)
        else:
            return etree.tostring(xml_element, encoding="utf8")
        
    

    def verificar_digest_value(xml_signed_path, element_id):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(xml_signed_path, parser)
        root = tree.getroot()

        element = root.find(".//*[@Id='%s']" % element_id)
        if element is None:
            element = root.find(".//*[@id='%s']" % element_id)
        if element is None:
            raise ValueError("Elemento com Id='%s' não encontrado no XML." % element_id)

        ns = {"ds": "http://www.w3.org/2000/09/xmldsig#"}
        signature = root.find(".//ds:Signature", namespaces=ns)
        if signature is None:
            raise ValueError("Elemento Signature não encontrado no XML.")

        digest_value_elem = signature.find(".//ds:DigestValue", namespaces=ns)
        if digest_value_elem is None or digest_value_elem.text is None:
            raise ValueError("DigestValue não encontrado na assinatura.")
        digest_value_xml = digest_value_elem.text.strip()

        c14n_element = etree.tostring(element, method="c14n", exclusive=False, with_comments=False)

        import hashlib
        import base64
        digest = hashlib.sha1(c14n_element).digest()
        digest_b64 = base64.b64encode(digest)

        print("DigestValue %s do XML: %s" % (element_id, digest_value_xml))
        print("DigestValue %s calculado: %s" % (element_id, digest_b64))

        if digest_value_xml == digest_b64:
            print("DigestValue está CORRETO.")
            return True
        else:
            print("DigestValue está INCORRETO!")
            return False

    xml_file = "teste.xml"
    id_elemento1 = "lote:1"
    id_elemento2 = "rps:11"
    # verificar_digest_value(xml_file, id_elemento1)
    # verificar_digest_value(xml_file, id_elemento2)
