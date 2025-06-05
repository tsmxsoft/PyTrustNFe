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

    def assina_xml(self, xml_element, reference, reference_lote, getchildren=False, **kwargs):
        cert, key = self.extract_cert_key()

        signer = XMLSigner(
            method=signxml.methods.enveloped,
            signature_algorithm="rsa-sha1",
            digest_algorithm="sha1",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
        )

        print('reference', reference)

        ns = {}
        ns[None] = signer.namespaces['ds']
        signer.namespaces = ns

        if reference:
            element = xml_element.find(".//*[@id='%s']" % (reference))
            if element is None:
                element = xml_element.find(".//*[@Id='%s']" % (reference))

            if element is not None:
                signed_root = signer.sign(
                    element, key=key.encode(), cert=cert.encode(),
                    reference_uri='#%s' % reference
                )

                signature = signed_root.findall(".//{http://www.w3.org/2000/09/xmldsig#}Signature")[-1]

                parent = element.getparent()
                if parent is not None and signature is not None:
                    parent.append(signature)

                if kwargs.get('include_ref'):
                    signature.set(kwargs['include_ref'], reference)

                if kwargs.get('remove_attrib'):
                    element.attrib.pop(kwargs['remove_attrib'], None)

        if reference_lote:
            element_lote = xml_element.find(".//*[@id='%s']" % (reference_lote))
            if element_lote is None:
                element_lote = xml_element.find(".//*[@Id='%s']" % (reference_lote))

            if element_lote is not None:
                signed_root_lote = signer.sign(
                    element_lote, key=key.encode(), cert=cert.encode(),
                    reference_uri='#%s' % reference_lote
                )

                signature_lote = signed_root_lote.findall(".//{http://www.w3.org/2000/09/xmldsig#}Signature")[-1]

                parent_lote = element_lote.getparent()
                if parent_lote is not None and signature_lote is not None:
                    parent_lote.append(signature_lote)

                if kwargs.get('include_ref'):
                    signature_lote.set(kwargs['include_ref'], reference_lote)

        if sys.version_info[0] > 2:
            return etree.tostring(xml_element, encoding=str)
        else:
            return etree.tostring(xml_element, encoding="utf8")
