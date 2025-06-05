# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import signxml
from lxml import etree
from pytrustnfe.certificado import extract_cert_and_key_from_pfx
from signxml import XMLSigner as XMLSignerOriginal
import sys

class XMLSigner(XMLSignerOriginal):
    def check_deprecated_methods(self):
        pass


class Assinatura(object):

    def __init__(self, arquivo, senha):
        self.arquivo = arquivo
        self.senha = senha

    def assina_xml(self, xml_element, reference, getchildren=False, **kwargs):
        cert, key = extract_cert_and_key_from_pfx(self.arquivo, self.senha)

        for element in xml_element.iter("*"):
            if element.text is not None and not element.text.strip():
                element.text = None

        signer = XMLSigner(
            method=signxml.methods.enveloped,
            signature_algorithm="rsa-sha1",
            digest_algorithm='sha1',
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315#WithComments",)

        if not 'sign_namespace' in kwargs:
            ns = {}
            ns[None] = signer.namespaces['ds']
            signer.namespaces = ns

        ref_uri = ('#%s' % reference) if reference else None
        element = xml_element.find(".//*[@id='%s']" % (reference))
        if element is None:
            element = xml_element.find(".//*[@Id='%s']" % (reference))
        if element is None:
            element = xml_element if xml_element.attrib['id'] == reference else None
        if element is None:
            element = xml_element if xml_element.attrib['Id'] == reference else None

        signed_root = signer.sign(
            element, key=key.encode(), cert=cert.encode(),
            reference_uri=ref_uri)

        if reference:
            sign_root = False
            element_signed = xml_element.find(".//*[@id='%s']" % (reference))
            if element_signed is None:
                element_signed = xml_element.find(".//*[@Id='%s']" % (reference))
            if element_signed is None:
                element_signed = xml_element if xml_element.attrib['id'] == reference else None
                sign_root = True
            if element_signed is None:
                element_signed = xml_element if xml_element.attrib['Id'] == reference else None
                sign_root = True
            
            signature = signed_root.findall(".//{http://www.w3.org/2000/09/xmldsig#}Signature")[-1]

            if kwargs.get('include_ref'):
                signature.set(kwargs['include_ref'], reference)

            if element_signed is not None and signature is not None:
                if sign_root:
                    element_signed.append(signature)
                else:
                    parent = element_signed.getparent()
                    parent.append(signature)

            if kwargs.get('remove_attrib'):
                element_signed.attrib.pop(kwargs['remove_attrib'], None)

        if sys.version_info[0] > 2:
            return etree.tostring(xml_element, encoding=str)
        else:
            return etree.tostring(xml_element, encoding="utf8")