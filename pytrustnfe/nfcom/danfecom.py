# -*- coding: utf-8 -*-
# © 2017 Edson Bernardino, ITK Soft
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# Classe para geração de PDF da DANFE a partir de xml etree.fromstring

import decimal
import os
import sys
from io import BytesIO
from textwrap import wrap
import math
from copy import copy
from reportlab.graphics.barcode import qr

from reportlab.lib import utils
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, gray, lightgrey, white
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import Paragraph, Image, KeepInFrame, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode import qr
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.common import I2of5
import pytz
from datetime import datetime, timedelta
from dateutil import parser as dateparser

if sys.version_info >= (3, 0):
    unicode = str


def chunks(cString, nLen):
    for start in range(0, len(cString), nLen):
        yield cString[start : start + nLen]


def format_cnpj_cpf(value):
    if len(value) < 12:  # CPF
        cValue = "%s.%s.%s-%s" % (value[:-8], value[-8:-5], value[-5:-2], value[-2:])
    else:
        cValue = "%s.%s.%s/%s-%s" % (
            value[:-12],
            value[-12:-9],
            value[-9:-6],
            value[-6:-2],
            value[-2:],
        )
    return cValue


def getdateByTimezone(cDateUTC, timezone=None):
    """
    Esse método trata a data recebida de acordo com o timezone do
    usuário. O seu retorno é dividido em duas partes:
    1) A data em si;
    2) As horas;
    :param cDateUTC: string contendo as informações da data
    :param timezone: timezone do usuário do sistema
    :return: data e hora convertidos para a timezone do usuário
    """

    # Aqui cortamos a informação do timezone da string (+03:00)
    dt = cDateUTC[0:19]

    # Verificamos se a string está completa (data + hora + timezone)
    if timezone and len(cDateUTC) == 25:

        # tz irá conter informações da timezone contida em cDateUTC
        tz = cDateUTC[19:25]
        tz = int(tz.split(":")[0])

        dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")

        # dt agora será convertido para o horario em UTC
        dt = dt - timedelta(hours=tz)

        # tzinfo passará a apontar para <UTC>
        dt = pytz.utc.localize(dt)

        # valor de dt é convertido para a timezone do usuário
        dt = timezone.normalize(dt)
        dt = dt.strftime("%Y-%m-%dT%H:%M:%S")

    cDt = dt[0:10].split("-")
    cDt.reverse()
    return "/".join(cDt), dt[11:16]


def format_number(cNumber, precision=0, group_sep=".", decimal_sep=","):
    if cNumber:
        number = decimal.Decimal(cNumber).normalize()
        return (
            ("{:,." + str(precision) + "f}")
            .format(number)
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    return ""


def tagtext(oNode=None, cTag=None):
    try:
        xpath = ".//{http://www.portalfiscal.inf.br/nfcom}%s" % (cTag)
        cText = oNode.find(xpath).text
    except:
        cText = ""
    return cText


REGIME_TRIBUTACAO = {
    "1": u"Simples Nacional",
    "2": u"Simples Nacional, excesso sublimite de receita bruta",
    "3": u"Regime Normal",
}


def get_image(path, width=1 * cm):
    img = utils.ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect))

def fmoney(value):
    try:
        v = str(value).replace(',','.').split('.')
        v1 = v[0]
        v2 = v[1]
        value = "R$ %s,%s" % (v1, v2)
    except Exception as e:
        print(e)
        pass

    return value

def dot_separated(number_str):
    # Reverse the string to insert dots, then insert a dot every three digits
    reversed_str = number_str[::-1]
    separated_str = '.'.join(reversed_str[i:i+3] for i in range(0, len(reversed_str), 3))
    # Reverse back to the original order
    return separated_str[::-1]

def round_decimal(number, decimal_places=2):
    # Ensure the decimal_places is within the range [2, 8]
    decimal_places = max(2, min(decimal_places, 8))
    
    # Create a Decimal object with the appropriate context for rounding
    decimal_number = decimal.Decimal(str(number))
    rounded_number = decimal_number.quantize(decimal.Decimal('1.' + '0' * decimal_places), rounding=decimal.ROUND_HALF_EVEN)
    
    # Format the number as a string with the specified decimal places
    #formatted_str = "{:0.*f}".format(decimal_places, rounded_number)
    formatted_str = "{:0.{dp}f}".format(rounded_number, dp=decimal_places)
    
    # Split the string into whole and decimal parts
    whole, dec = formatted_str.split('.') if '.' in formatted_str else (formatted_str, '')
    
    # Insert dots as thousand separators and replace the dot with a comma in the decimal part
    whole_part = dot_separated(whole)
    dec = dec.rstrip('0')
    
    # Combine the whole and decimal parts and return the formatted string
    result = whole_part + (',00' if dec in [0,''] else ',' + dec)
    return result

class DANFECom(object):
    def __init__(
        self,
        sizepage=A4,
        list_xml=None,
        orientation="portrait",
        logo=None,
        cce_xml=None,
        timezone=None,
        area_contrib_prioritario='',
        area_contrib='',
    ):
        path = os.path.join(os.path.dirname(__file__), "fonts")
        imgpath = os.path.join(os.path.dirname(__file__), "images")
        pdfmetrics.registerFont(
            TTFont("NimbusSanL-Regu", os.path.join(path, "NimbusSanL Regular.ttf"))
        )
        pdfmetrics.registerFont(
            TTFont("NimbusSanL-Bold", os.path.join(path, "NimbusSanL Bold.ttf"))
        )
        self.width = 210  # 21 x 29,7cm
        self.height = 297
        self.nLeft = 10
        self.nRight = 10
        self.nTop = 7
        self.nBottom = 8
        self.nlin = self.nTop
        self.logo = logo or imgpath + "/logoNFCOM.png"
        self.area_contrib = area_contrib
        self.area_contrib_prioritario = area_contrib_prioritario
        self.oFrete = {
            "0": "0 - Contratação por conta do Remetente (CIF)",
            "1": "1 - Contratação por conta do Destinatário (FOB)",
            "2": "2 - Contratação por conta de Terceiros",
            "3": "3 - Transporte Próprio por conta do Remetente",
            "4": "4 - Transporte Próprio por conta do Destinatário",
            "9": "9 - Sem Ocorrência de Transporte",
        }

        self.oPDF_IO = BytesIO()
        if orientation == "landscape":
            raise NameError("Rotina não implementada")
        else:
            size = sizepage

        self.canvas = canvas.Canvas(self.oPDF_IO, pagesize=size)
        self.canvas.setTitle("DANFECom")
        self.canvas.setStrokeColor(black)
        self.maxprod = 10

        for oXML in list_xml:
            self.NrPages = 1
            self.Page = 1

            el_det = oXML.findall(".//{http://www.portalfiscal.inf.br/nfcom}det")

            # Declaring variable to prevent future errors
            nId = 0

            if el_det is not None:
                list_desc = []
                list_cod_prod = []

                for nId, item in enumerate(el_det):
                    el_prod = item.find(".//{http://www.portalfiscal.inf.br/nfcom}prod")
                    infAdProd = item.find(
                        ".//{http://www.portalfiscal.inf.br/nfcom}infAdProd"
                    )

                    list_ = wrap(tagtext(oNode=el_prod, cTag="xProd"), 50)
                    if infAdProd is not None:
                        list_.extend(wrap(infAdProd.text, 50))
                    list_desc.append(list_)

                    list_cProd = wrap(tagtext(oNode=el_prod, cTag="cProd"), 14)
                    list_cod_prod.append(list_cProd)

                # Calculando nr. aprox. de páginas
                if nId > self.maxprod:
                    self.NrPages += math.ceil(nId/(self.maxprod*5)) + 1

            self.ide_emit(oXML=oXML, timezone=timezone)
            self.destinatario(oXML=oXML, timezone=timezone)

            #self.detalhamentos(oXML=oXML, timezone=timezone)
            index = self.detalhamentos(
                oXML=oXML,
                el_det=el_det,
                max_index=min((self.maxprod*5),nId),
                list_desc=list_desc,
                list_cod_prod=list_cod_prod,
            )
            for np in range(1,int(self.NrPages)):
                p2 = nId
                self.newpage()
                self.ide_emit(oXML=oXML, timezone=timezone)
                if index > p2:
                    break
                index = self.detalhamentos(
                    oXML=oXML,
                    el_det=el_det,
                    index=index,
                    max_index=p2,
                    list_desc=list_desc,
                    list_cod_prod=list_cod_prod,
                )
                self.nlin = self.height - 36

                if index >= p2:
                    self.newpage()
                    self.ide_emit(oXML=oXML, timezone=timezone)
                    break

            self.detalhamentos_resumo(oXML=oXML, timezone=timezone)
            self.info_complementares(oXML=oXML, timezone=timezone)
            self.area_contrib_cliente(oXML=oXML, timezone=timezone)
            self.area_anatel(oXML=oXML, timezone=timezone)

            self.tarjas(oXML=oXML)
            self.newpage()
        if cce_xml:
            for xml in cce_xml:
                self._generate_cce(cce_xml=xml, oXML=oXML, timezone=timezone)
                self.newpage()
        self.canvas.save()

    def tarjas(self,oXML=None):
        #Tarjas
        elem_ide = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}ide")
        elem_evento = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}infEvento")
        #Homologação
        if tagtext(oNode=elem_ide, cTag="tpAmb") == "2":
            self.canvas.saveState()
            self.canvas.rotate(90)
            self.canvas.setFont("Times-Bold", 40)
            self.canvas.setFillColorRGB(0.57, 0.57, 0.57)
            self.string(self.nLeft + 65, 449, "SEM VALOR FISCAL")
            self.canvas.restoreState()

        # Cancelado
        if tagtext(oNode=elem_evento, cTag="cStat") in ("135", "155"):
            self.canvas.saveState()
            self.canvas.rotate(45)
            self.canvas.setFont("NimbusSanL-Bold", 60)
            self.canvas.setFillColorRGB(1, 0.2, 0.2)
            self.string(self.nLeft + 80, 275, "CANCELADO")
            self.canvas.restoreState()

    def draw_qr_code(self, string, nlin):
        qr_code = qr.QrCodeWidget(string)
        drawing = Drawing(25 * mm, 25 * mm)
        drawing.add(qr_code)
        renderPDF.draw(drawing, self.canvas, (self.nLeft + 65) * mm, (self.height - nlin - 30) * mm)

    def ide_emit(self, oXML=None, timezone=None):
        elem_emit = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}emit")

        self.canvas.setLineWidth(0.5)
        self.canvas.setFillColor(lightgrey)
        self.canvas.setStrokeColor(gray)
        self.rect(self.nLeft, self.nlin + 2, self.width - self.nLeft - self.nRight, 32, True)
        self.canvas.setFillColor(black)
        
        # Labels
        styles = getSampleStyleSheet()
        styleN = styles["Normal"]
        styleN.fontSize = 8
        styleN.fontName = "NimbusSanL-Bold"
        styleN.alignment = TA_LEFT

        if self.logo:
            img = get_image(self.logo, width=2 * cm)
            img.drawOn(
                self.canvas, (self.nLeft + 5) * mm, (self.height - self.nlin - 20) * mm
            )
        cEnd = u"DOCUMENTO AUXILIAR DA NOTA FISCAL FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA"
        cEnd += u"<br/><br/>%s<br/>" % (tagtext(oNode=elem_emit, cTag="xNome"))
        cEnd += "CNPJ: " + format_cnpj_cpf(tagtext(oNode=elem_emit, cTag="CNPJ")) + "<br />"
        if tagtext(oNode=elem_emit, cTag="IE"):
            cEnd += "IE: " + tagtext(oNode=elem_emit, cTag="IE") + "<br />"
        cEnd += (
            tagtext(oNode=elem_emit, cTag="xLgr")
            + ", "
            + tagtext(oNode=elem_emit, cTag="nro")
            + " - "
        )
        cEnd += tagtext(oNode=elem_emit, cTag="xCpl") + " - "
        cEnd += (
            tagtext(oNode=elem_emit, cTag="xBairro")
            + "<br />"
            + tagtext(oNode=elem_emit, cTag="xMun")
            + " - "
        )
        cEnd += (
            tagtext(oNode=elem_emit, cTag="UF")
            + " - "
            + tagtext(oNode=elem_emit, cTag="CEP")
        )

        styleN.fontName = "NimbusSanL-Regu"
        styleN.fontSize = 7
        styleN.leading = 10
        P = Paragraph(cEnd, styleN)
        w, h = P.wrap(130 * mm, 20 * mm)
        P.drawOn(
            self.canvas, (self.nLeft + 30) * mm, (self.height - self.nlin - 30) * mm
        )

        self.nlin += 36

    def destinatario(self, oXML=None, timezone=None):
        elem_ide = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}ide")
        elem_dest = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}dest")
        elem_assinante = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}assinante")
        elem_ender_dest = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}enderDest")
        elem_fat = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}gFat")
        elem_total = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}total")
        nMr = self.width - self.nRight
        
        styles = getSampleStyleSheet()
        styleN = styles["Normal"]
        styleN.fontSize = 6
        styleN.fontName = "NimbusSanL-Bold"
        styleN.alignment = TA_LEFT

        self.nlin += 2
        offset = self.nlin

        # labels
        self.canvas.setFont("NimbusSanL-Bold", 6)
        self.string(self.nLeft, self.nlin, "CLIENTE:")
        self.nlin += 1

        # Conteúdo campos
        self.canvas.setFont("NimbusSanL-Regu", 8)
        self.string(
            self.nLeft, self.nlin + (self.nlin-offset)*2.5, tagtext(oNode=elem_dest, cTag="xNome")
        )
        self.nlin += 1
        self.canvas.setFont("NimbusSanL-Regu", 6)
        cnpj_cpf = tagtext(oNode=elem_dest, cTag="CNPJ")
        if cnpj_cpf:
            cnpj_cpf = "CNPJ: " + format_cnpj_cpf(cnpj_cpf)
        elif tagtext(oNode=elem_dest, cTag="CPF"):
            cnpj_cpf = "CPF: " + format_cnpj_cpf(tagtext(oNode=elem_dest, cTag="CPF"))
        else:
            cnpj_cpf = tagtext(oNode=elem_dest, cTag="idOutros")
        self.string(self.nLeft, self.nlin + (self.nlin-offset)*2.5, cnpj_cpf)
        self.nlin += 2
        
        ie = tagtext(oNode=elem_dest, cTag="IE")
        im = tagtext(oNode=elem_dest, cTag="IM")
        
        if ie:
            self.string(self.nLeft, self.nlin + (self.nlin-offset)*1.7, "IE: " + ie)
            self.nlin += 1
        if im:
            self.string(self.nLeft, self.nlin + (self.nlin-offset)*1.7, "IM: " + im)
            self.nlin += 1
        self.nlin += 1
        
        #labels
        self.canvas.setFont("NimbusSanL-Bold", 6)
        self.string(self.nLeft, self.nlin + (self.nlin-offset)*1.5, "ENDEREÇO:")
        self.nlin += 1

        #Endereço
        cEnd = (
            tagtext(oNode=elem_dest, cTag="xLgr")
            + ", "
            + tagtext(oNode=elem_dest, cTag="nro")
            + " - "
        )
        cEnd += tagtext(oNode=elem_dest, cTag="xCpl") + " - "
        cEnd += (
            tagtext(oNode=elem_dest, cTag="xBairro")
            + "<br />"
            + tagtext(oNode=elem_dest, cTag="xMun")
            + " - "
        )
        cEnd += (
            tagtext(oNode=elem_dest, cTag="UF")
            + " - "
            + tagtext(oNode=elem_dest, cTag="CEP")
        )
        styleN.fontName = "NimbusSanL-Regu"
        styleN.fontSize = 6
        styleN.leading = 8
        P = Paragraph(cEnd, styleN)
        w, h = P.wrap(100 * mm, 20 * mm)
        P.drawOn(
            self.canvas, (self.nLeft) * mm, (self.height - (self.nlin + (self.nlin-offset)*1.4) - 5) * mm
        )
        self.nlin += 2

        #labels
        self.canvas.setFont("NimbusSanL-Bold", 6)
        self.string(self.nLeft, self.nlin + (self.nlin-offset)*2.0, "INFORMAÇÕES:")
        self.nlin += 1
        #Conteudo
        self.canvas.setFont("NimbusSanL-Regu", 6)
        self.string(self.nLeft, self.nlin + (self.nlin-offset)*2.0, "Cod. Assinante: " + tagtext(oNode=elem_assinante, cTag="iCodAssinante"))
        self.nlin += 1
        tel = tagtext(oNode=elem_ender_dest, cTag="fone")
        if tel:
            self.string(self.nLeft, self.nlin + (self.nlin-offset)*2.0, "Telefone: " + tel)
            self.nlin += 1
        periodo = "%s à %s" %(
            datetime.strptime(tagtext(oNode=elem_fat,cTag="dPerUsoIni"),"%Y-%m-%d").strftime("%d/%m/%Y"),
            datetime.strptime(tagtext(oNode=elem_fat,cTag="dPerUsoFim"),"%Y-%m-%d").strftime("%d/%m/%Y"),
        )
        self.string(self.nLeft, self.nlin + (self.nlin-offset)*2.0, "Período: %s" % periodo)
        self.nlin += 1

        #REFERENCIA (ANO/MES)
        self.canvas.setStrokeColor(gray)
        self.canvas.setFillColor(white)
        self.rect(self.nLeft, self.nlin + (self.nlin-offset)*2.0, (self.width - self.nLeft - self.nRight)/3, 6, fill=True, stroke=True)
        self.canvas.setFillColor(black)
        refmes = datetime.strptime(tagtext(oNode=elem_fat,cTag="CompetFat"),"%Y%m").strftime("%m/%Y")
        self.string(self.nLeft + 3, self.nlin + (self.nlin-offset)*2.0+3.5, "REFERÊNCIA (ANO/MÊS): %s" % refmes)
        self.nlin += 2

        #VENCIMENTO
        self.canvas.setStrokeColor(gray)
        self.canvas.setFillColor(white)
        self.rect(self.nLeft, self.nlin + (self.nlin-offset)*2.0+1, (self.width - self.nLeft - self.nRight)/3, 6, fill=True, stroke=True)
        self.canvas.setFillColor(black)
        venc = datetime.strptime(tagtext(oNode=elem_fat,cTag="dVencFat"),"%Y-%m-%d").strftime("%d/%m/%Y")
        self.string(self.nLeft + 3, self.nlin + (self.nlin-offset)*2.0+4.5, "VENCIMENTO: %s" % venc)
        self.nlin += 2

        #TOTAL A PAGAR
        self.canvas.setStrokeColor(gray)
        self.canvas.setFillColor(white)
        self.rect(self.nLeft, self.nlin + (self.nlin-offset)*2.0+2, (self.width - self.nLeft - self.nRight)/3, 6, fill=True, stroke=True)
        self.canvas.setFillColor(black)
        total = fmoney(tagtext(oNode=elem_total,cTag="vNF"))
        self.string(self.nLeft + 3, self.nlin + (self.nlin-offset)*2.0+5.5, "TOTAL A PAGAR: %s" % total)
        self.nlin += 2
        
        self.destinatario_col2(oXML,timezone,offset=offset)

        self.nlin += 36  # Nr linhas ocupadas pelo bloco

    def destinatario_col2(self, oXML=None, timezone=None, offset=None):
        elem_infnfcom = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}infNFCom")
        elem_emit = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}emit")
        elem_ide = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}ide")
        elem_infprot = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}infProt")

        nlin = offset or self.nlin
        elem_supl = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}infNFComSupl")

        #QRCode
        qrcod = tagtext(oNode=elem_supl, cTag="qrCodNFCom")
        if qrcod:
            self.draw_qr_code(qrcod,nlin)

        styles = getSampleStyleSheet()
        styleN = styles["Normal"]
        styleN.fontSize = 6
        styleN.leading = 6
        styleN.fontName = "NimbusSanL-Regu"
        styleN.alignment = TA_LEFT

        #Dados NFCom
        cEnd = u"NOTA FISCAL FATURA No. %s<br/>" % ("{0:011}".format(int(tagtext(oNode=elem_ide, cTag="nNF"))))
        cEnd += u"SÉRIE: " + tagtext(oNode=elem_ide, cTag="serie") + "<br /><br />"
        cEnd += u"DATA DE EMISSÃO: " + dateparser.parse(tagtext(oNode=elem_ide, cTag="dhEmi")).strftime("%d/%m/%Y as %H:%I:%S") + "<br /><br />"
        cEnd += u"CONSULTE PELA CHAVE DE ACESSO EM:<br />http://dfe-porta.sefazvirtual.rs.gov.br/NFCom<br /><br />"
        chavenfcom = elem_infnfcom.attrib["Id"][5:]
        cEnd += u"CHAVE DE ACESSO:<br /> %s" % (
            ' '.join(chavenfcom[i:i+4] for i in range(0, len(chavenfcom), 4))
        )

        P = Paragraph(cEnd, styleN)
        w, h = P.wrap(150 * mm, 20 * mm)
        P.drawOn(
            self.canvas, (self.nLeft + 99) * mm, (self.height - nlin - 22) * mm
        )
        nlin += cEnd.count("<br")
        self.canvas.setFillColor(white)
        
        if elem_infprot is not None:
            self.canvas.setFillColor(black)
            self.string(self.nLeft + 99, nlin + 18, "Protocolo de Autorização: %s - %s" %(
                tagtext(oNode=elem_infprot, cTag="nProt"),
                dateparser.parse(tagtext(oNode=elem_infprot, cTag="dhRecbto")).strftime("%d/%m/%Y as %H:%I:%S%z")
            ))
            nlin += 1

        #Área do contribuinte
        self.canvas.setFillColor(white)
        self.canvas.setStrokeColor(lightgrey)
        self.rect(self.nLeft + 65, 81, ((self.width - self.nLeft - self.nRight)/1.5)-2, 20, fill=True, stroke=True)
        self.canvas.setFillColor(black)
        self.canvas.setFont("NimbusSanL-Bold", 6)
        self.string(self.nLeft + 68, 83, "ÁREA DO CONTRIBUINTE:")
        nlin += 2
        
        if self.area_contrib is not None:
            self.area_contrib = self.area_contrib.replace("\n","<br/>")
            P = Paragraph(self.area_contrib, styleN)
            w, h = P.wrap(((self.width - self.nLeft - self.nRight)/0.6) * mm, 10 * mm)
            frame = KeepInFrame(w, h, [P], mode='truncate')
            frame.width = (self.width - self.nLeft - self.nRight)/0.6
            frame.height = 15 * mm
            frame.drawOn(self.canvas, (self.nLeft + 68) * mm, (self.height - nlin - self.area_contrib.count('<br') - 38) * mm)
        
        self.canvas.setFont("NimbusSanL-Regu", 6)
        self.canvas.setFillColor(black)

    def detalhamentos(
        self,
        oXML=None,
        el_det=None,
        index=0,
        max_index=0,
        list_desc=None,
        list_cod_prod=None,
        nHeight=28,
    ):
        nMr = self.width - self.nRight
        nStep = 2.5  # Passo entre linhas
        nH = 28 * nStep
        self.nlin += 1
        # nH é o altura da linha vertical, utilizar como referência
        # somar a ele a altura atual que é nlin
        maxHeight = self.nlin + max_index + nH

        lineHeight = 4.0 + ((max_index-index+1) * 3.5)
        self.canvas.setFont("NimbusSanL-Regu", 5.5)
        # Colunas
        self.stringcenter(self.nLeft + 20.5, self.nlin + 4.5, "ITENS")
        self.stringcenter(nMr - 80, self.nlin + 4.5, "UN")
        self.stringcenter(nMr - 70, self.nlin + 4.5, "QTD")
        self.stringcenter(nMr - 60, self.nlin + 4.5, "V. UNIT.")
        self.stringcenter(nMr - 50, self.nlin + 4.5, "TOTAL")
        self.stringcenter(nMr - 37, self.nlin + 4.5, "PIS/COFINS")
        self.stringcenter(nMr - 25, self.nlin + 4.5, "BC. ICMS")
        self.stringcenter(nMr - 15, self.nlin + 4.5, "ALIQ")
        self.stringcenter(nMr - 5, self.nlin + 4.5, "V. ICMS")

        self.hline(self.nRight, self.nlin + 2, self.width - self.nLeft)
        self.hline(self.nRight, self.nlin + 6, self.width - self.nLeft)

        nLin = copy(self.nlin) + 9
        id = copy(index)

        self.vline(nMr - 85, self.nlin + 2, lineHeight)
        self.vline(nMr - 75, self.nlin + 2, lineHeight)
        self.vline(nMr - 65, self.nlin + 2, lineHeight)
        self.vline(nMr - 55, self.nlin + 2, lineHeight)
        self.vline(nMr - 45, self.nlin + 2, lineHeight)
        self.vline(nMr - 30, self.nlin + 2, lineHeight)
        self.vline(nMr - 20, self.nlin + 2, lineHeight)
        self.vline(nMr - 10, self.nlin + 2, lineHeight)
        self.vline(nMr, self.nlin + 2, lineHeight)
        self.vline(self.nRight, self.nlin + 2, lineHeight)

        # Conteúdo campos
        self.canvas.setFont("NimbusSanL-Regu", 5)

        while id <= max_index:
            item = el_det[id]
            piscofins  = decimal.Decimal(tagtext(oNode=item, cTag="vPIS") or 0) or decimal.Decimal(0)
            piscofins += decimal.Decimal(tagtext(oNode=item, cTag="vCOFINS") or 0) or decimal.Decimal(0)
            
            aliquota  = decimal.Decimal(tagtext(oNode=item, cTag="pICMS") or 0) or decimal.Decimal(0)
            aliquota += decimal.Decimal(tagtext(oNode=item, cTag="pFCP") or 0) or decimal.Decimal(0)
            
            icms  = decimal.Decimal(tagtext(oNode=item, cTag="vICMS") or 0) or decimal.Decimal(0)
            icms += decimal.Decimal(tagtext(oNode=item, cTag="vFCP") or 0) or decimal.Decimal(0)

            codprod = tagtext(oNode=item, cTag="cProd")[:60]
            descprod = tagtext(oNode=item, cTag="xProd")[:120]
            self.string(nMr - 187, nLin, codprod)
            self.string(nMr - len(codprod) - 175, nLin, descprod[:100-len(codprod)])

            self.stringcenter(nMr - 80, nLin, tagtext(oNode=item, cTag="uMed"))
            self.stringcenter(nMr - 70, nLin, tagtext(oNode=item, cTag="qFaturada"))
            self.stringcenter(nMr - 60, nLin, round_decimal(decimal.Decimal(tagtext(oNode=item, cTag="vItem")), 8))
            self.stringcenter(nMr - 50, nLin, round_decimal(decimal.Decimal(tagtext(oNode=item, cTag="vProd")), 8))
            self.stringcenter(nMr - 37, nLin, round_decimal(piscofins, 2))
            self.stringcenter(nMr - 25, nLin, round_decimal(decimal.Decimal(tagtext(oNode=item, cTag="vBC")), 8))
            self.stringcenter(nMr - 15, nLin, round_decimal(decimal.Decimal(aliquota * 100), 4) + '%')
            self.stringcenter(nMr - 5, nLin, round_decimal(decimal.Decimal(icms), 8))

            #TODO: Fazer o codigo do item e produto quebrar linha
            #TODO: Segue abaixo o exemplo da danfe
            # # Código Item
            # line_cod = nLin
            # for des in list_cod_prod[id]:
            #     self.string(self.nLeft + 0.2, line_cod, des)
            #     line_cod += nStep

            # # Descrição Item
            # line_desc = nLin
            # for des in list_desc[id]:
            #     self.string(self.nLeft + 15.5, line_desc, des)
            #     line_desc += nStep

            nLin += nStep
            self.canvas.setStrokeColor(gray)
            self.hline(self.nLeft, nLin - 2, self.width - self.nLeft)
            self.canvas.setStrokeColor(black)
            
            id += 1
            nLin += 1

        self.nlin = nLin
        return id

    def detalhamentos_resumo(self, oXML=None, timezone=None):
        oXML_infadic = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}infAdic")
        oXML_ide = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}ide")
        oXML_total = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}total")
        self.nlin += 2

        #col 1
        data = [
            ('VALOR NFF', 'R$' + round_decimal(decimal.Decimal(tagtext(oNode=oXML_total, cTag="vNF")), 8)),
            ('TOTAL BASE DE CALCULO', 'R$' + round_decimal(decimal.Decimal(tagtext(oNode=oXML_total, cTag="vBC")), 8)),
            ('VALOR ICMS', 'R$' + round_decimal(decimal.Decimal(tagtext(oNode=oXML_total, cTag="vICMS")), 8)),
            ('VALOR ISENTO', 'R$' + round_decimal(decimal.Decimal(tagtext(oNode=oXML_total, cTag="vDesc")), 8)),
            ('VALOR OUTROS', 'R$' + round_decimal(decimal.Decimal(tagtext(oNode=oXML_total, cTag="vOutro")), 8)),
        ]
        t = Table(data,[None for x in range(len(data[0]))],[None for x in range(len(data))])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("FONT", (1, 0), (1, -1), "NimbusSanL-Regu"),
            ("FONT", (0, 0), (0, -1), "NimbusSanL-Bold"),
            ("ALIGN", (1, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ('BACKGROUND', (0,0), (0,len(data)), lightgrey),
            ('GRID', (0,0), (len(data[0]),len(data)), 1, black),
        ]))
        t.wrapOn(self.canvas, ((self.width - self.nLeft - self.nRight)/4) * mm, 450)
        t.drawOn(self.canvas, self.nLeft * mm, 122*mm)
        
        #col 2
        data = [
            ('INFORMAÇÕES DOS TRIBUTOS', ''),
            ('TRIBUTO', 'VALOR'),
            ('PIS', 'R$' + round_decimal(decimal.Decimal(tagtext(oNode=oXML_total, cTag="vPIS")), 8)),
            ('COFINS', 'R$' + round_decimal(decimal.Decimal(tagtext(oNode=oXML_total, cTag="vCOFINS")), 8)),
            ('FUST', 'R$' + round_decimal(decimal.Decimal(tagtext(oNode=oXML_total, cTag="vFUST")), 8)),
            ('FUNTTEL', 'R$' + round_decimal(decimal.Decimal(tagtext(oNode=oXML_total, cTag="vFUNTTEL")), 8)),
        ]
        t = Table(data,[None for x in range(len(data[0]))],[15 for x in range(len(data))])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 6),
            ("FONT", (0, 2), (1, -1), "NimbusSanL-Regu"),
            ("FONT", (0, 0), (1, 1), "NimbusSanL-Bold"),
            ("ALIGN", (1, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0,0), (1, -1), "MIDDLE"),
            ('BACKGROUND', (0,0), (1,1), lightgrey),
            ('GRID', (0,0), (len(data[0]),len(data)), 1, black),
            ('SPAN', (0,0), (1, 0)),
        ]))
        t.wrapOn(self.canvas, ((self.width - self.nLeft - self.nRight)/4) * mm, 450)
        t.drawOn(self.canvas, (self.nLeft + 53) * mm, 122*mm)
        
        #col 3
        texto_fisco = ''
        if oXML_infadic:
            texto_fisco = tagtext(oNode=oXML_infadic, cTag='infAdFisco').replace('\n', '<br/>')[:3000]
        if tagtext(oNode=oXML_ide, cTag='tpEmis') == '2':
            texto_fisco = "EMITIDO EM CONTINGÊNCIA <br/> Pendente de autorização"
        styles = getSampleStyleSheet()
        styleN = styles["BodyText"]
        styleN.fontSize = 6
        styleN.leading = 8
        
        ptexto_fisco = Paragraph(texto_fisco, styleN)
        w, h = ptexto_fisco.wrap(((self.width - self.nLeft - self.nRight)) * mm, 450)
        frame_ptexto_fisco = KeepInFrame(w, h, [ptexto_fisco], mode='truncate')
        frame_ptexto_fisco.width = ((self.width - self.nLeft - self.nRight)) * mm
        frame_ptexto_fisco.height = 450
        
        data = [
            ('RESERVADO AO FISCO', ''),
            (frame_ptexto_fisco, ''),
        ]
        t = Table(data,[140,140],[10,80])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (1, 1), 6),
            ("FONT", (0, 0), (1, 0), "NimbusSanL-Bold"),
            ("FONT", (0, 1), (1, 1), "NimbusSanL-Regu"),
            ("TOPPADDING", (0, 0), (1, 0), 6),
            ("VALIGN", (0,0), (1, 0), "MIDDLE"),
            ("VALIGN", (0,1), (1, 1), "TOP"),
            ("ALIGN", (0, 0), (1, 0), "CENTER"),
            ("ALIGN", (0, 1), (1, 1), "LEFT"),
            ('BACKGROUND', (0,0), (1,0), lightgrey),
            ('GRID', (0,0), (len(data[0]),len(data)), 1, black),
            ('SPAN', (0,0), (1, 0)),
            ('SPAN', (0,1), (1, 1)),
        ]))
        t.wrapOn(self.canvas, ((self.width - self.nLeft - self.nRight)) * mm, 450)
        t.drawOn(self.canvas, (self.nLeft + 91) * mm, 122*mm)
        self.nlin += 5

    def info_complementares(self, oXML=None, timezone=None):
        oXML_infadic = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}infAdic")

        texto_fisco = ''
        if oXML_infadic:
            texto_fisco = tagtext(oNode=oXML_infadic, cTag='infCpl').replace('\n', '<br/>')[:3000]
        styles = getSampleStyleSheet()
        styleN = styles["BodyText"]
        styleN.fontSize = 6
        styleN.leading = 0
        
        ptexto_fisco = Paragraph(texto_fisco, styleN)
        w, h = ptexto_fisco.wrap(((self.width - self.nLeft - self.nRight)) * mm, 450)
        frame_ptexto_fisco = KeepInFrame(w, h, [ptexto_fisco], mode='truncate')
        frame_ptexto_fisco.width = ((self.width - self.nLeft - self.nRight)) * mm
        frame_ptexto_fisco.height = 450
        
        data = [
            ('INFORMAÇÕES COMPLEMENTARES', ''),
            (frame_ptexto_fisco, ''),
        ]
        t = Table(data,[269,269],[10,80])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (1, 1), 6),
            ("FONT", (0, 0), (1, 0), "NimbusSanL-Bold"),
            ("FONT", (0, 1), (1, 1), "NimbusSanL-Regu"),
            ("TOPPADDING", (0, 0), (1, 0), 6),
            ("VALIGN", (0,0), (1, 0), "MIDDLE"),
            ("VALIGN", (0,1), (1, 1), "TOP"),
            ("ALIGN", (0, 0), (1, 0), "CENTER"),
            ("ALIGN", (0, 1), (1, 1), "LEFT"),
            ('BACKGROUND', (0,0), (1,0), lightgrey),
            ('GRID', (0,0), (len(data[0]),len(data)), 1, black),
            ('SPAN', (0,0), (1, 0)),
            ('SPAN', (0,1), (1, 1)),
        ]))
        t.wrapOn(self.canvas, ((self.width - self.nLeft - self.nRight)) * mm, 450)
        t.drawOn(self.canvas, (self.nLeft) * mm, 88 * mm)
        self.nlin += 22

    def area_contrib_cliente(self, oXML=None, timezone=None):
        oXML_gfat = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}gFat")

        styles = getSampleStyleSheet()

        styleL = copy(styles["Normal"])
        styleL.fontSize = 6
        styleL.leading = 6
        styleL.alignment = TA_CENTER
        styleL.fontName = "NimbusSanL-Bold"

        styleN = copy(styles["Normal"])
        styleN.fontSize = 8
        styleN.leading = 12
        styleN.alignment = TA_CENTER
        styleN.fontName = "NimbusSanL-Regu"

        #col1
        P1 = Paragraph("Nº IDENTIFICADOR DE DÉBITO AUTOMÁTICO<br/><br/>", styleL)
        w, h = P1.wrap(100 * mm, 6 * mm)

        coddeb = tagtext(oNode=oXML_gfat, cTag="codDebAuto")
        P2 = Paragraph(coddeb, styleN)
        w, h2 = P2.wrap(100 * mm, 6 * mm)

        frame_ptexto_ident_debauto = KeepInFrame(w, h+h2+6
                                                 , [P1,P2], mode='truncate')
        
        #col2
        itens = []
        bcH = 0
        P3 = Paragraph("CODIGO DE BARRAS<br/><br/><br/>", styleL)
        w, h = P1.wrap(((self.width - self.nLeft - self.nRight)/0.2) * mm, 6 * mm)
        itens.append(P3)
        bcH += h

        codbar = tagtext(oNode=oXML_gfat, cTag="codBarras")
        if codbar:
            altura = 13 * mm
            comprimento = 100 * mm
            tracoFino = 0.254320987654 * mm  # Tamanho correto aproximado

            bc = I2of5(
                codbar,
                barWidth=tracoFino,
                barHeight=altura,
                bearers=0,
                quiet=1,
                ratio=3,
                checksum=0,
            )
            
            tracoFino = (tracoFino * comprimento) / bc.width
            bc.__init__(codbar, barWidth=tracoFino)
            
            bcH += altura
            itens.append(bc)
            
            P4 = Paragraph(str(codbar), styleN)
            w, h = P4.wrap(((self.width - self.nLeft - self.nRight)/0.2) * mm, 6 * mm)
            bcH += h
            
            itens.append(P4)

        frame_bc = KeepInFrame(280, bcH+6, itens, mode='shrink',hAlign='CENTER',vAlign='MIDDLE')

        #col3
        itens = []
        bcH = 0
        styleL.fontSize = 12
        P3 = Paragraph("PIX<br/><br/><br/>", styleL)
        w, h = P3.wrap(((self.width - self.nLeft - self.nRight)/0.2) * mm, 6 * mm)
        itens.append(P3)
        bcH += h

        pix = tagtext(oNode=oXML_gfat, cTag="urlQRCodePIX")
        if pix:
            bc = qr.QrCode(
                pix,width=96, height=96
            )
            
            bcH += altura
            itens.append(bc)

        frame_pix = KeepInFrame(50, bcH+6, itens, mode='shrink',hAlign='CENTER',vAlign='MIDDLE')

        data = [
            ('ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL', '', ''),
            (frame_ptexto_ident_debauto, frame_bc, frame_pix),
        ]
        t = Table(data,[100,338,100],[10,70])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (1, 1), 6),
            ("FONT", (0, 0), (1, 0), "NimbusSanL-Bold"),
            ("FONT", (0, 1), (1, 1), "NimbusSanL-Regu"),
            ("TOPPADDING", (0, 0), (1, 0), 6),
            ("VALIGN", (0,0), (0, 0), "MIDDLE"),
            ("VALIGN", (0,1), (2, 1), "TOP"),
            ("ALIGN", (0, 0), (2, 0), "CENTER"),
            ("ALIGN", (0, 1), (2, 1), "CENTER"),
            ('BACKGROUND', (0,0), (2,0), lightgrey),
            ('GRID', (0,0), (len(data[0]),len(data)), 1, black),
            ('SPAN', (0,0), (2, 0)),
        ]))
        t.wrapOn(self.canvas, ((self.width - self.nLeft - self.nRight)) * mm, 250)
        t.drawOn(self.canvas, (self.nLeft) * mm, 58 * mm)
        self.nlin += 22

    def area_anatel(self, oXML=None, timezone=None):
        styles = getSampleStyleSheet()
        styleN = styles["BodyText"]
        styleN.fontSize = 6
        styleN.leading = 8

        ptexto_fisco = Paragraph(self.area_contrib_prioritario, styleN)
        w, h = ptexto_fisco.wrap(((self.width - self.nLeft - self.nRight)) * mm, 450)
        frame_ptexto_fisco = KeepInFrame(w, h, [ptexto_fisco], mode='truncate')
        frame_ptexto_fisco.width = ((self.width - self.nLeft - self.nRight)) * mm
        frame_ptexto_fisco.height = 450
        
        data = [
            ('ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL', ''),
            (frame_ptexto_fisco, ''),
        ]
        t = Table(data,[269,269],[10,80])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (1, 1), 6),
            ("FONT", (0, 0), (1, 0), "NimbusSanL-Bold"),
            ("FONT", (0, 1), (1, 1), "NimbusSanL-Regu"),
            ("TOPPADDING", (0, 0), (1, 0), 6),
            ("VALIGN", (0,0), (1, 0), "MIDDLE"),
            ("VALIGN", (0,1), (1, 1), "TOP"),
            ("ALIGN", (0, 0), (1, 0), "CENTER"),
            ("ALIGN", (0, 1), (1, 1), "LEFT"),
            ('BACKGROUND', (0,0), (1,0), lightgrey),
            ('GRID', (0,0), (len(data[0]),len(data)), 1, black),
            ('SPAN', (0,0), (1, 0)),
            ('SPAN', (0,1), (1, 1)),
        ]))
        t.wrapOn(self.canvas, ((self.width - self.nLeft - self.nRight)) * mm, 450)
        t.drawOn(self.canvas, (self.nLeft) * mm, 25 * mm)
        self.nlin += 22

    def newpage(self):
        self.nlin = self.nTop
        self.Page += 1
        self.canvas.showPage()

    def hline(self, x, y, width):
        y = self.height - y
        self.canvas.line(x * mm, y * mm, width * mm, y * mm)

    def vline(self, x, y, width):
        width = self.height - y - width
        y = self.height - y
        self.canvas.line(x * mm, y * mm, x * mm, width * mm)

    def rect(self, col, lin, nWidth, nHeight, fill=False, stroke=True):
        lin = self.height - nHeight - lin
        self.canvas.rect(
            col * mm, lin * mm, nWidth * mm, nHeight * mm, stroke=stroke, fill=fill
        )

    def roundRect(self, col, lin, nWidth, nHeight, fill=False, stroke=True, radius=1):
        lin = self.height - nHeight - lin
        self.canvas.roundRect(
            col * mm, lin * mm, nWidth * mm, nHeight * mm, stroke=stroke, fill=fill, radius=radius
        )

    def string(self, x, y, value):
        y = self.height - y
        self.canvas.drawString(x * mm, y * mm, value)

    def stringRight(self, x, y, value):
        y = self.height - y
        self.canvas.drawRightString(x * mm, y * mm, value)

    def stringcenter(self, x, y, value):
        y = self.height - y
        self.canvas.drawCentredString(x * mm, y * mm, value)

    def writeto_pdf(self, fileObj):
        pdf_out = self.oPDF_IO.getvalue()
        self.oPDF_IO.close()
        fileObj.write(pdf_out)

    def _generate_cce(self, cce_xml=None, oXML=None, timezone=None):
        self.canvas.setLineWidth(0.2)

        # labels
        self.canvas.setFont("NimbusSanL-Bold", 12)
        self.stringcenter(105, 10, u"Carta de Correção")
        self.canvas.setFont("NimbusSanL-Regu", 6)
        self.string(10, 18, u"RAZÃO SOCIAL DO EMITENTE")
        self.string(10, 24, u"CNPJ DO EMITENTE")
        self.string(10, 30, u"CHAVE DE ACESSO DA NF-E")
        self.string(10, 36, u"DATA DA CORREÇÃO")
        self.string(10, 42, u"ID")
        self.stringcenter(105, 48, u"CORREÇÃO")

        # lines
        self.hline(9, 14, 200)
        self.hline(9, 20, 200)
        self.hline(9, 26, 200)
        self.hline(9, 32, 200)
        self.hline(9, 38, 200)
        self.hline(9, 44, 200)
        self.hline(9, 50, 200)

        # values
        infNFCom = oXML.find(".//{http://www.portalfiscal.inf.br/nfcom}infNFCom")
        res_partner = infNFCom.find(".//{http://www.portalfiscal.inf.br/nfcom}xNome")

        elem_infNFCom = cce_xml.find(".//{http://www.portalfiscal.inf.br/nfcom}infEvento")

        res_partner = tagtext(oNode=infNFCom, cTag="xNome")
        self.string(82, 18, res_partner)
        cnpj = format_cnpj_cpf(tagtext(oNode=elem_infNFCom, cTag="CNPJ"))
        self.string(82, 24, cnpj)
        chave_acesso = tagtext(oNode=elem_infNFCom, cTag="chNFCom")
        self.string(82, 30, chave_acesso)
        data_correcao = getdateByTimezone(
            tagtext(oNode=elem_infNFCom, cTag="dhEvento"), timezone
        )
        data_correcao = data_correcao[0] + "  " + data_correcao[1]
        self.string(82, 36, data_correcao)
        cce_id = elem_infNFCom.values()[0]
        self.string(82, 42, cce_id)

        correcao = tagtext(oNode=elem_infNFCom, cTag="xCorrecao")

        w, h, paragraph = self._paragraph(
            correcao, "NimbusSanL-Regu", 10, 190 * mm, 20 * mm
        )
        paragraph.drawOn(self.canvas, 10 * mm, (297 - 52) * mm - h)

        self.hline(9, 54 + (h / mm), 200)
        self.stringcenter(105, 58 + (h / mm), u"CONDIÇÃO DE USO")
        self.hline(9, 60 + (h / mm), 200)

        condicoes = tagtext(oNode=elem_infNFCom, cTag="xCondUso")

        w2, h2, paragraph = self._paragraph(
            condicoes, "NimbusSanL-Regu", 10, 190 * mm, 20 * mm
        )
        paragraph.drawOn(self.canvas, 10 * mm, (297 - 62) * mm - h - h2)

        self.hline(9, 68 + ((h + h2) / mm), 200)

        self.vline(80, 14, 30)
        self.vline(9, 14, 54 + ((h + h2) / mm))
        self.vline(200, 14, 54 + ((h + h2) / mm))

    def _paragraph(self, text, font, font_size, x, y):
        ptext = "<font size=%s>%s</font>" % (font_size, text)
        style = ParagraphStyle(name="Normal", fontName=font, fontSize=font_size,)
        paragraph = Paragraph(ptext, style=style)
        w, h = paragraph.wrapOn(self.canvas, x, y)
        return w, h, paragraph
