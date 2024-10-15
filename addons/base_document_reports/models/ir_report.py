# -*- coding:utf-8 -*-

import os
import re
import io
import subprocess
import base64
import jinja2
import tempfile
import logging
from docxtpl import InlineImage

from num2words import num2words
from docxtpl import DocxTemplate
from odoo import fields, models, api
from odoo.tools.misc import formatLang
from datetime import datetime
from odoo.tools.misc import format_datetime, format_date, get_lang
from odoo.addons.base_document_reports.controllers.report_record import ReportRecordWebController
from odoo.tools import pdf
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ReportAction(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(
        selection_add=[("docx", "DOCX")],
        ondelete={'docx': 'set default'}
    )
    show_wizard = fields.Boolean(string='Show Wizard', default=False)
    report_res_model = fields.Char()
    report_res_id = fields.Integer()

    def _record_to_json(self, record, **kw):
        report_record = ReportRecordWebController()
        return report_record._parse_record_to_dict(record)

    def render_docx(self, doc_ids, data):
        """ Reference Document: https://docxtpl.readthedocs.io/en/latest/
        """
        context = self.env.context
        template = context.get('report_template')
        # Currently single document supported, limiting to one record only
        records = self.env[context.get('report_model')].sudo().search([('id', 'in', doc_ids)])
        pdf_content = []
        if len(records) > 1:
            if template.output_type != 'pdf':
                output_type = dict(template._fields["output_type"].selection).get(template.output_type)
                raise UserError(
                    "Printing of {OUTPUT_TYPE} type reports for multiple records is not supported.".format(OUTPUT_TYPE=output_type))
            for record in records:
                content, report_name = self.render_docx_template_data(template, record)
                pdf_content.append(content)
            if pdf_content:
                pdf_content = pdf.merge_pdf(pdf_content)
                report_name = template.name
            return pdf_content, report_name
        else:
            return self.render_docx_template_data(template, records)

    @api.model
    def _render_docx(self, doc_ids, data):
        docx_template_id = self.env['docx.template'].sudo().search([('report_id', '=', self.id)], limit=1)
        if docx_template_id:
            record = self.env[docx_template_id.model_name].sudo().browse(doc_ids)
            return self.render_docx_template_data(docx_template_id, record)

    def render_docx_template_data(self, docx_template_id, record, data=False, output_type=False):
        data = base64.b64decode(data or docx_template_id.docx_file)
        # Store docx file data in buffer and create DocxTemplate
        file_buffer = io.BytesIO(data)
        doc = DocxTemplate(file_buffer)

        doc_context = {}

        if self.env.context.get('ReportOutputType'):
            doc_context.update({'ReportOutputType': self.env.context.get('ReportOutputType')})
        if not docx_template_id.lazy_load:
            doc_context.update(docx_template_id.convert_to_dict(record, docx_template=doc))
        else:
            doc_context.update({
                'obj': record,
                'load_image': self._to_image,
                'html_to_text': self._html_to_text,
                'amount_with_currency': self._currency_with_symbol,
                'selection_value': self._show_label,
                'format_date': self._format_date,
                'format_datetime': self._format_datetime,
                'doc': doc,
                'docx_template_id': docx_template_id,
                'user': self.env.user,
                'datetime': datetime.now()
            })

        # Adding footer print log of user and datetime
        # NOTE: Call this before rendering doc
        doc = docx_template_id._add_print_log(doc)

        # Add custom filters to the Jinja environment
        jinja_env = jinja2.Environment()
        jinja_env.filters['num2words'] = num2words

        # Render dynamic data with custom environment
        doc.render(doc_context, jinja_env)

        # Save file in tmp folder and close the buffer
        temp_file = '/tmp/%s' % (int(fields.Datetime.now().timestamp()))
        doc.save('%s.docx' % temp_file)
        file_buffer.close()
        if output_type == 'pdf' or docx_template_id.output_type == 'pdf':
            file_name = '%s.pdf' % temp_file
            command = ["libreoffice", "--headless", "--convert-to", "pdf", "%s.docx" % temp_file, '--outdir', '/tmp']
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                _logger.error(f"Unable to convert docx to pdf {result.stderr.decode('utf-8')}")
        else:
            file_name = '%s.docx' % temp_file

        _logger.info(f"Output file generated under {file_name} and reading for export")
        file_text = open(file_name, 'rb')
        pdf_content = file_text.read()
        file_text.close()

        # Remove files from /tmp folder if exists
        if os.path.exists('%s.docx' % temp_file):
            os.remove('%s.docx' % temp_file)
        if os.path.exists('%s.pdf' % temp_file):
            os.remove('%s.pdf' % temp_file)

        report_name = 'pdf'
        if self.env.context.get('report_name'):
            report_name = '{} - {}'.format(record.name, docx_template_id.name)
        return pdf_content, report_name

    #  DOCUMENT SUPPORTING METHODS

    def _to_image(self, doc, base64_datas):
        # FIXME: Check with File streaming
        tmp_img_file = tempfile.NamedTemporaryFile(delete=None, suffix='.jpg')
        tmp_img_file.write(base64.b64decode(base64_datas))
        record_value = InlineImage(doc, tmp_img_file.name)
        tmp_img_file.close()
        return record_value

    def _html_to_text(self, html_value):
        # Removing <br> with \n
        html_value = str(html_value or '').replace("<br>", "\n")
        # and removing all HTML tags
        return re.sub(r'<[^<]+?>', '', html_value)

    def _currency_with_symbol(self, obj, amount_value, currency_field='currency_id'):
        currency_obj = obj[currency_field] if currency_field in obj else self.env.company.currency_id
        return formatLang(self.env, amount_value, currency_obj=currency_obj)

    def _show_label(self, obj, field):
        key = obj[field]
        return dict(obj._fields[field]._description_selection(self.env)).get(key)

    def _format_date(self, date):
        return format_date(self.env, date, lang_code=get_lang(self.env).code, date_format=False)

    def _format_datetime(self, datetime):
        tz = self.env.user.tz
        if (self.env.user._is_public() or self.env.user._is_system()):
            tz = self.env.company.tz
        return format_datetime(self.env, datetime, tz=tz, lang_code=get_lang(self.env).code, dt_format=False)
