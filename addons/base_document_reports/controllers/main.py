# -*- coding: utf-8 -*-

import json
import base64
import werkzeug
import PyPDF2
import traceback
import logging

from io import BytesIO
from odoo import http
from odoo.http import request, content_disposition
from odoo.tools import html_escape
from odoo.addons.web.controllers.main import ReportController
from odoo.addons.web.controllers.main import _serialize_exception


_logger = logging.getLogger(__name__)


class ReportControllerDocx(ReportController):

    @http.route(['/report/docx/download'], type='http', auth="user")
    def report_docx_download(self, data, context=None):
        report = request.env['ir.actions.report']
        request_content = json.loads(data)
        url, action_id = request_content[0], request_content[2]
        context = json.loads(context)
        try:
            pattern = '/report/docx/'
            doc_ids = url.split(pattern)[0].split('/')[2]
            doc_ids = [int(doc_id) for doc_id in doc_ids.split(',')]
            template = request.env['docx.template'].sudo().search([('report_id', '=', action_id)])
            template_data = base64.b64decode(template.docx_file)
            context.update({
                'report_template': template,
                'report_model': template.model_name,
                'report_name': template.name,
                'report_output_type': template.output_type
            })
            raw_content, report_name = report.with_context(context).render_docx(doc_ids, data=template_data)
            content_disposition_data = content_disposition('%s.%s' % (report_name, template.output_type))

            return request.make_response(raw_content, [
                ('Content-Type', 'application/octet-stream'),
                ('Content-Length', len(raw_content)),
                ('Content-Disposition', content_disposition_data)
            ])

        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Server Error",
                'data': se
            }
            res = request.make_response(html_escape(json.dumps(error)))
            raise werkzeug.exceptions.InternalServerError(response=res) from e

    @http.route()
    def report_routes(self, reportname, docids=None, converter=None, **data):

        template = False
        document_output_type = converter
        try:
            report_model = data.get('report_model', 'ir.actions.report')

            context = json.loads(data.get('context', '{}'))

            # Default QWeb Reports
            if converter == 'pdf' and report_model == 'ir.actions.report':
                if not docids and 'active_ids' in context and context.get('active_ids'):
                    docids = ','.join([str(id) for id in context.get('active_ids', [])])
                report = request.env['ir.actions.report'].browse(int(reportname)).report_name if reportname.isdigit() else reportname
                return super().report_routes(report, docids, converter, **data)

            doc_ids = [int(doc_id) for doc_id in docids.split(',')] if docids else context.get('active_ids', [])

            template = request.env[report_model].sudo().browse(int(reportname)) if reportname.isdigit() else request.env.ref(reportname)

            document_output_type = data.get('report_output_type', 'pdf')
            pdf = template.with_context(ReportOutputType=data.get('report_output_type')).render_document_report(doc_ids)[0]
            repeat = int(data.get('has_repeat_count', 0))
            if repeat > 0:
                pdf = self.repeat_pdf(pdf, repeat)

        except Exception as e:
            se = _serialize_exception(e)
            traceback_msg = traceback.format_exc()
            _logger.error(traceback_msg)
            pdf = request.env['ir.actions.report']._run_wkhtmltopdf(['Oops! Please connect Tech Support. <br/><h2>%s</h2>' % (se.get('message'))], se.get('message'))

        content_disposition_data = content_disposition('%s.%s' % (template and template.name or 'TechSupport', document_output_type or 'pdf'))
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)), ('Content-Disposition', content_disposition_data)]

        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route('/report/<converter>/<reportname>/<docids>/<report_model>/<context>')
    def report_context_routes(self, reportname, docids=None, converter=None, report_model=None, context='', **data):
        data = data or {}
        data.update({
            'context': context.replace("'", '"'),
            'report_model': report_model
        })
        return self.report_routes(reportname=reportname, docids=docids, converter=converter, **data)

    def repeat_pdf(self, pdf_bytes, num_merges):
        writer = PyPDF2.PdfFileWriter()
        for _ in range(num_merges):
            reader = PyPDF2.PdfFileReader(BytesIO(pdf_bytes))

            for page_num in range(reader.numPages):
                page = reader.getPage(page_num)
                writer.addPage(page)

        output_bytes = BytesIO()
        writer.write(output_bytes)
        return output_bytes.getvalue()
