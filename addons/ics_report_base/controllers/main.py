# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.addons.web.controllers.main import ReportController
from werkzeug.urls import url_decode


class WebReportController(ReportController):

    @http.route()
    def report_download(self, data, context=None):
        response = super().report_download(data, context=context)

        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]

        if type not in ['qweb-pdf', 'qweb-text']:
            return response

        if len(url.split('?')) > 1:
            data = dict(url_decode(url.split('?')[1]).items())

            # Checking for custom request from the data as print_report_name and
            # overriding the filename
            if 'options' in data:
                options = json.loads(data.get('options'))
                if 'print_report_name' in options:
                    extension = 'pdf' if type == 'qweb-pdf' else 'txt'
                    filename = options.get('print_report_name')
                    response.headers.set('Content-Disposition', http.content_disposition("{}.{}".format(filename, extension)))

        return response
