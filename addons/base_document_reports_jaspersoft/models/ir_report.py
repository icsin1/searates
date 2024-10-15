# -*- coding:utf-8 -*-
import base64
import json
import tempfile
from pyreportjasper import PyReportJasper
from odoo import fields, models


class ReportAction(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(
        selection_add=[("jrxml", "Jasper (JRXML)")],
        ondelete={'jrxml': 'cascade'}
    )

    def render_jrxml_template_data(self, report_template, record, data=False, output_type=False):
        report_template_obj = report_template._find_template(record)
        template_data = base64.b64decode(data or report_template_obj.jrxml_file)
        py_jasper = PyReportJasper()
        record_json = self._record_to_json(record, json_spec=report_template_obj.json_spec_id)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as jspr_json_data:
            jspr_json_data.write(json.dumps(record_json))
            jspr_json_data.flush()
            conn = {
                'driver': 'json',
                'data_file': jspr_json_data.name
            }
            with tempfile.NamedTemporaryFile() as jspr_input_file:
                jspr_input_file.write(template_data)
                jspr_input_file.flush()
                jspr_output_file = '/tmp/%s' % (int(fields.Datetime.now().timestamp()))
                py_jasper.config(
                    jspr_input_file.name,
                    jspr_output_file,
                    output_formats=["pdf"],
                    db_connection=conn
                )
                py_jasper.process_report()

                file_text = open(f'{jspr_output_file}.pdf', 'rb')
                pdf_content = file_text.read()
                file_text.close()

                report_name = '{} - {}.pdf'.format(record.name, report_template.name)
                return pdf_content, report_name

    def _record_to_json(self, record, json_spec=None):
        if json_spec:
            return json_spec._to_dict(record)
        return super()._record_to_json(record)
