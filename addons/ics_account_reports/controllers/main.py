# -*- coding: utf-8 -*-
import json
from werkzeug.exceptions import InternalServerError
from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools.misc import html_escape


class ReportController(http.Controller):

    @http.route('/download_content', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report(self, report_name, output_format, model, report_id, options, **kw):
        try:
            report = request.env[model]
            options = json.loads(options)
            folded = kw.get('folded')
            if isinstance(folded, str):
                options['folded'] = False if folded == 'false' else True
            else:
                options['folded'] = bool(folded)
            options['show_ageing'] = bool(kw.get('show_ageing'))
            ctx = json.loads(kw.get('context', '{}'))
            if report_id and report_id != 'false':
                report = request.env[model].browse(int(report_id))
            report = report.with_context(ctx)
            report_name = '{}.{}'.format(report_name, output_format)

            if output_format == 'xlsx':
                file_datas = report.get_excel(options)
                mimetype = 'application/vnd.ms-excel'
            if output_format == 'pdf':
                file_datas = report.get_pdf(options)
                mimetype = 'application/pdf'

            response = request.make_response(file_datas, headers=[
                    ('Content-Type', mimetype),
                    ('Content-Disposition', content_disposition(report_name))
                ]
            )
            return response
        except Exception as e:
            error = {
                'code': 200,
                'message': 'Server Error',
                'data': _serialize_exception(e)
            }
            res = request.make_response(html_escape(json.dumps(error)))
            raise InternalServerError(response=res) from e
