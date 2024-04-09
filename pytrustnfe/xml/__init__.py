# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree,objectify
from jinja2 import Environment, FileSystemLoader
from . import filters

import sys


def recursively_empty(e):
    if e.text:
        return False
    return all((recursively_empty(c) for c in e.iterchildren()))


def render_xml(path, template_name, remove_empty, remove_newline = True, **nfe):
    nfe = recursively_normalize(nfe)
    env = Environment(loader=FileSystemLoader(
        path))
    env.filters["normalize"] = filters.strip_line_feed
    env.filters["normalize_str"] = filters.normalize_str
    env.filters["format_percent"] = filters.format_percent
    env.filters["format_datetime"] = filters.format_datetime
    env.filters["format_datetime_dmy"] = filters.format_datetime_dmy
    env.filters["format_datetime_ymd"] = filters.format_datetime_ymd
    env.filters["format_datetime_wslashes_ymd"] = filters.format_datetime_wslashes_ymd
    env.filters["format_datetime_hms"] = filters.format_datetime_hms
    env.filters["format_numeric"] = filters.format_numeric
    env.filters["format_cep"] = filters.format_cep
    env.filters["format_date"] = filters.format_date
    env.filters["comma"] = filters.format_with_comma

    template = env.get_template(template_name)
    xml = template.render(**nfe)
    if remove_newline:
        xml = xml.replace("\n", "")
    parser = etree.XMLParser(
        remove_blank_text=True, remove_comments=True, strip_cdata=False
    )
    root = etree.fromstring(xml, parser=parser)
    for element in root.iter("*"):  # remove espaços em branco
        if element.text is not None and not element.text.strip():
            element.text = None
    if remove_empty:
        context = etree.iterwalk(root)
        for dummy, elem in context:
            parent = elem.getparent()
            if recursively_empty(elem):
                parent.remove(elem)

    if sys.version_info[0] > 2:
        return etree.tostring(root, encoding=str)
    else:
        return etree.tostring(root, encoding="utf8")


def sanitize_response(response):
    parser = etree.XMLParser(encoding="utf-8")
    if sys.version_info[0] < 3:
        if isinstance(response,unicode):
            response = response.encode("UTF-8")
    tree = etree.fromstring(response, parser=parser)
    # Remove namespaces inuteis na resposta
    for elem in tree.getiterator():
        if not hasattr(elem.tag, "find"):
            continue
        i = elem.tag.find("}")
        if i >= 0:
            elem.tag = elem.tag[i + 1:]
    objectify.deannotate(tree, cleanup_namespaces=True)
    xml_str = ""
    xml_obj = None
    try:
        xml_str = etree.tostring(tree)
        xml_obj = objectify.fromstring(xml_str)
    except:
        pass
    return response, xml_obj


def recursively_normalize(vals):
    for item in vals:
        if type(vals[item]) is str:
            vals[item] = vals[item].strip()
            vals[item] = filters.normalize_str(vals[item])
        elif type(vals[item]) is dict:
            recursively_normalize(vals[item])
        elif type(vals[item]) is list:
            for a in vals[item]:
                recursively_normalize(a)
    return vals
