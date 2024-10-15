import base64
import json
from odoo import models, fields, api


class ReportSampleDataDownloadWizard(models.TransientModel):
    _name = 'report.sample.data.download.wizard'
    _description = 'Sample Data Downloader'

    @api.model
    def _selection_target_model(self):
        model_name = self.env.context.get('default_record_model')
        return [(model_name, model_name)]

    report_res_model = fields.Char()
    report_res_id = fields.Many2oneReference(string='Related Report', model_field='report_res_model')
    report_model_id = fields.Many2one('ir.model', string='Model')
    report_model_name = fields.Char(related='report_model_id.model', store=True, string='Report Model')
    resource_ref = fields.Reference('_selection_target_model', 'Related Document', required=True)

    def action_download_data(self):
        self.ensure_one()
        report = self.env[self.report_res_model].sudo().browse(self.report_res_id)
        record_dict = report.report_id.sudo()._record_to_json(self.resource_ref)
        report.sample_data_file = base64.b64encode(json.dumps(record_dict).encode('utf-8'))
        return {
            'type': 'ir.actions.act_url',
            'name': 'Sample Data File',
            'target': 'self',
            'url': '/web/content/%s/%s/sample_data_file/sample_data.json?download=true' % (report._name, report.id),
        }
