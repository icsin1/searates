# -*- coding: utf-8 -*-

import json
from werkzeug.exceptions import InternalServerError
from odoo.http import content_disposition, request
from odoo import http
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools.misc import html_escape
from odoo.addons.ics_account_reports.controllers.main import ReportController


class ReportControllerInherit(ReportController):

    @http.route('/download_content', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report(self, report_name, output_format, model, report_id, options, **kw):
        """ Override method for download CSV report for GSTR """
        try:
            file_datas = False
            report = request.env[model]
            options = json.loads(options)
            ctx = json.loads(kw.get('context', '{}'))
            if report_id and report_id != 'false':
                report = request.env[model].browse(int(report_id))
            report = report.with_context(ctx)
            if output_format == 'csv':
                file_datas = report.get_csv(options)
                mimetype = 'text/csv'
            if file_datas:
                response = request.make_response(file_datas, headers=[
                    ('Content-Type', mimetype),
                    ('Content-Disposition', content_disposition(report_name))
                ])
                return response
            else:
                return super().get_report(report_name, output_format, model, report_id, json.dumps(options), **kw)
        except Exception as e:
            error = {
                'code': 200,
                'message': 'Server Error',
                'data': _serialize_exception(e)
            }
            res = request.make_response(html_escape(json.dumps(error)))
            raise InternalServerError(response=res) from e
