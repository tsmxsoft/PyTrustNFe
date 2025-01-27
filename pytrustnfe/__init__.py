# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

def get_version():
    return "1.0.292"

class HttpClient(object):
    def __init__(self, url):
        self.url = url

    def _headers(self, action):
        return {
            "Content-type": "text/xml; charset=utf-8;",
            "Accept": "application/soap+xml; charset=utf-8",
            "SOAPAction": action,
        }

    def post_soap(self, xml_soap, action):
        import requests

        header = self._headers(action)
        res = requests.post(self.url, data=xml_soap, headers=header)
        return res.text
