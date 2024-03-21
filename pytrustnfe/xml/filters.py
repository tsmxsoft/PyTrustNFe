# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from decimal import Decimal
from datetime import date
from datetime import datetime
from unicodedata import normalize
from jinja2.exceptions import UndefinedError
import sys


def normalize_str(string):
    """
    Remove special characters and strip spaces
    """
    if string:
        if not isinstance(string, str):
            string = str(string, "utf-8", "replace")

        string = string.encode("utf-8")
        return (
            normalize("NFKD", string.decode("utf-8")).encode("ASCII", "ignore").decode()
        )
    return ""


def strip_line_feed(string):
    if string:
        if sys.version_info[0] > 2:
            if not isinstance(string, str):
                string = str(string, "utf-8", "replace")
        else:
            if not isinstance(string,unicode):
                string = unicode(string, "utf-8")
        remap = {
            ord("\t"): " ",
            ord("\n"): " ",
            ord("\f"): " ",
            ord("\r"): None,  # Delete
        }
        return string.translate(remap).strip()
    return string


def format_percent(value):
    if value:
        return Decimal(value) / 100


def format_datetime(value):
    """
    Format datetime
    """
    dt_format = "%Y-%m-%dT%H:%M:%I"
    if isinstance(value, datetime):
        return value.strftime(dt_format)
    return value

def format_datetime_dmy(value):
    """
    format datetime string 
    to day/month/year string
    """
    obj = datetime.strptime(value,"%Y-%m-%dT%H:%M:%S")
    return obj.strftime("%d/%m/%Y")



def format_datetime_ymd(value):
    """
    format datetime string 
    to day/month/year string
    """
    obj = datetime.strptime(value,"%Y-%m-%dT%H:%M:%S")
    return obj.strftime("%Y-%m-%d")

def format_datetime_wslashes_ymd(value):
    """
    format datetime string 
    to day/month/year string
    """
    obj = datetime.strptime(value,"%Y%m%dT%H%M%S")
    return obj.strftime("%Y-%m-%d")

def format_numeric(value, digits, decimals = 2, has_dot = True, replace_comma = False):
    """
    format numeric (int or decimal)
    to decimal, with dot or not, replacing dot to comma or not
    and padding zero left if needed
    """
    obj = "%.{0}f".format(decimals) % Decimal(value)
    #if should have a dot, but haven't
    if not "." in obj and has_dot:
        obj = obj[:len(obj)-3] + "." + obj[len(obj)-3:]
    #if shouldn't have a dot
    if "." in obj and not has_dot:
        obj = obj.replace('.','')
    elif "." in obj and replace_comma:
        obj = obj.replace('.',',')
    #zero left
    if len(obj) < digits:
        obj = obj.zfill(digits)
    return obj

def format_datetime_hms(value):
    """
    format datetime string 
    to hour:minute:second string
    """
    obj = datetime.strptime(value,"%Y-%m-%dT%H:%M:%S")
    return obj.strftime("%H:%M:%S")

def format_cep(value):
    """
    format CEP (ZIP Code Brazil) int (or string)
    to 99999-999 string
    """
    cep = str(value)
    if len(cep) == 8:
        return cep[:5] + "-" + cep[5:]
    return cep

def format_date(value):
    """
    Format date
    """
    try:
        dt_format = "%Y-%m-%d"
        if isinstance(value, date):
            return value.strftime(dt_format)
        return value
    except UndefinedError:
        return ''
    except Exception:
        return value


def format_with_comma(value):
    try:
        if isinstance(value, float):
            return ("%.2f" % value).replace(".", ",")
        else:
            return ("%.2f" % float(value)).replace(".",",")
        return value
    except UndefinedError:
        return ''
    except Exception:
        return value