import xmlschema
import os
from lxml import etree

VERSION = "1.00"



def _render(cert, method, **kwargs):
    xsd_file = os.path.join(os.path.dirname(__file__), 'xsds/' + method + '_v' + VERSION + '.xsd')
    schema = xmlschema.XMLSchema(xsd_file)