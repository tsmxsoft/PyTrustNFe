# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from OpenSSL import crypto
import signxml
from lxml import etree
from signxml import XMLSigner,XMLVerifier
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

        signer.namespaces = {None: signxml.namespaces.ds}
        ref_uri = ('#%s' % reference) if reference else None

        element = xml_element.find(".//*[@id='%s']" % (reference))
        if element is None:
            element = xml_element.find(".//*[@Id='%s']" % (reference))
        signed_root = signer.sign(
            element, key=key.encode(), cert=cert.encode(),
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
            return etree.tostring(xml_element, encoding=str, method='html')
        else:
            return etree.tostring(xml_element, encoding="utf8", method='html')