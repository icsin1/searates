# -*- coding:utf-8 -*-
import base64
import subprocess
import tempfile
from pathlib import Path
from odoo import fields, models
from odoo.http import request
from odoo.exceptions import ValidationError


class ReportAction(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(
        selection_add=[("mrt", "Stimulsoft (MRT)")],
        ondelete={'mrt': 'cascade'}
    )

    def _render_mrt(self, res_ids=None, data=None):
        """ Called by other then action where it will auto render as pdf instead of HTML Preview """
        self_sudo = self.sudo()
        mrt_report = self.env['stimulsoft.mrt.report'].search([('report_id', '=', self_sudo.id)], limit=1)
        if res_ids and mrt_report:
            Model = self.env[self_sudo.model]
            records = Model.browse(res_ids)
            pdf_content, pdf_file_name = self.render_mrt_template_data(mrt_report, records)
            return pdf_content, 'pdf'
        return None

    def _record_to_json(self, record, json_spec=None):
        ctx = self.env.context
        if json_spec:
            return json_spec.with_context(ctx)._to_dict(record)
        return super()._record_to_json(record)

    def render_mrt_template_data(self, report_template, record, data=False, output_type=False):
        report_template_obj = report_template._find_template(record)

        # Calling NODEJS for Stimulsoft
        module_path = Path(__file__)
        node_script_path = '{}/static/src/libs/stimulsoft-nodejs/stimulsoft-nodejs-pdf.js'.format(module_path.parent.parent)
        # base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        # Run the Node.js script using subprocess
        result = subprocess.run([
            'node',
            node_script_path,
            "{},{}".format(report_template_obj._name, report_template_obj.id),  # template
            "{},{}".format(record._name, record.id),  # record
            request.session.sid
        ], capture_output=True, text=True)

        if result.returncode != 0:
            raise ValidationError(result.stderr)

        pdf_content_base64 = result.stdout

        if pdf_content_base64.startswith('ERROR: '):
            raise ValidationError(pdf_content_base64)

        with tempfile.NamedTemporaryFile() as pdf_content_file:
            pdf_content_file.write(base64.b64decode(pdf_content_base64))
            pdf_content_file.flush()

            file_data = open(f'{pdf_content_file.name}', 'rb')
            pdf_content = file_data.read()
            file_data.close()
            report_name = '{}.pdf'.format(report_template.name)
            if 'name' in record._fields:
                report_name = '{} - {}.pdf'.format(record.name, report_template.name)

            return pdf_content, report_name
