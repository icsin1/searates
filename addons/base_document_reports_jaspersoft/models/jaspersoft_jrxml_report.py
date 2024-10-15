from odoo import models, fields, _
from odoo.exceptions import UserError


class JaspserReportJRXMLReport(models.Model):
    _name = 'jaspersoft.jrxml.report'
    _inherit = 'mixin.report.template'
    _description = 'Jaspersoft JRXML Report'
    _template_field = 'jrxml_file'
    _report_type = 'jrxml'

    output_type = fields.Selection(selection_add=[
        ('pdf', 'PDF'),
    ], default='pdf', string='Output Type', required=True, ondelete={'pdf': 'cascade'})
    jrxml_file = fields.Binary(string='Template (.jrxml)')
    filename = fields.Char(string='Filename')
    json_spec_id = fields.Many2one('product.json.specification')
    freight_product_based_format = fields.Boolean(default=False, string='Product Based Reporting')
    product_report_ids = fields.One2many('jaspersoft.jrxml.report.product', 'report_id', 'Product Reports')

    def render_document_report(self, doc_ids, **kwargs):
        self.ensure_one()
        records = self.env[self.model_name].sudo().browse(doc_ids)
        return self.report_id.render_jrxml_template_data(self, records[0])

    def _find_template(self, record):
        self.ensure_one()
        if not self.freight_product_based_format:
            return self
        for product_report in self.product_report_ids:
            if product_report._is_matched(record):
                return product_report
        else:
            raise UserError(_('No Template found for {}'.format(self.res_model_id.name)))

    def action_download_spec(self):
        return self.json_spec_id.action_download_json_spec()

    def action_download_json_sample(self):
        action = super().action_download_json_sample()
        action['context'].update({
            'default_json_specification_id': self.json_spec_id.id
        })
        return action


class JaspserReportJRXMLReportProduct(models.Model):
    _name = 'jaspersoft.jrxml.report.product'
    _description = 'JRXML Product Template'
    _order = 'sequence'

    report_id = fields.Many2one('jaspersoft.jrxml.report', required=True, ondelete='cascade')
    product_id = fields.Many2one('freight.product', required=True)
    json_spec_id = fields.Many2one('product.json.specification', required=True)
    jrxml_file = fields.Binary(string='Template (.jrxml)')
    filename = fields.Char(string='Filename')
    sequence = fields.Integer(default=0)

    def _is_matched(self, records):
        domain = self.json_spec_id.get_product_domain() + [('id', 'in', records.ids)]
        return bool(self.env[self.report_id.res_model_id.model].sudo().search(domain, count=True))

    def action_download_spec(self):
        return self.json_spec_id.action_download_json_spec()

    def action_download_json_sample_product(self):
        self.ensure_one()
        action = self.env.ref('base_document_reports.sample_data_download_wizard_action').sudo().read([])[0]
        context = {
            'default_record_model': self.report_id.res_model_id.model,
            'default_report_model_id': self.report_id.res_model_id.id,
            'default_report_res_model': self.report_id._name,
            'default_report_res_id': self.report_id.id,
            'default_json_specification_id': self.json_spec_id.id
        }
        action['context'] = context
        return action
