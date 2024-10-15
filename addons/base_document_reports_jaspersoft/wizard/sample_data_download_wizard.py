import json
import base64
from odoo import models, fields, api


class ReportSampleDataDownloadWizard(models.TransientModel):
    _inherit = 'report.sample.data.download.wizard'

    json_specification_id = fields.Many2one('product.json.specification', string='JSON Specification')

    @api.onchange('resource_ref')
    def _onchange_resource_ref(self):
        if self.json_specification_id:
            return {'domain': {'resource_ref': self.json_specification_id.get_product_domain()}}

    def action_download_data(self):
        self.ensure_one()
        report = self.env[self.report_res_model].sudo().browse(self.report_res_id)
        record_dict = report.report_id.sudo()._record_to_json(self.resource_ref, self.json_specification_id)
        report.sample_data_file = base64.b64encode(json.dumps(record_dict).encode('utf-8'))
        return {
            'type': 'ir.actions.act_url',
            'name': 'Sample Data File',
            'target': 'self',
            'url': '/web/content/%s/%s/sample_data_file/sample_data.json?download=true' % (report._name, report.id),
        }
