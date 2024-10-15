from odoo import models, fields, _
from odoo.exceptions import UserError
import re
import ast


class StimulsoftMRTReport(models.Model):
    _name = 'stimulsoft.mrt.report'
    _inherit = 'mixin.report.template'
    _description = 'Stimulsoft MRT Report'
    _template_field = 'mrt_file'
    _report_type = 'mrt'

    mrt_file = fields.Binary(string='Template (.mrt)', required=True)
    filename = fields.Char(string='Filename')
    json_spec_id = fields.Many2one('product.json.specification')
    freight_product_based_format = fields.Boolean(default=False, string='Product Based Reporting')
    product_report_ids = fields.One2many('stimulsoft.mrt.report.product', 'report_id', 'Product Reports')
    document_type_id = fields.Many2one('freight.document.type', string='Document Type')
    output_type = fields.Selection(selection_add=[
        ('pdf', 'PDF'), ('html', 'HTML Preview')
    ], default='html', string='Output Type', required=True, ondelete={'pdf': 'cascade', 'html': 'set default'})

    def render_document_report(self, doc_ids, **kwargs):
        self.ensure_one()
        records = self.env[self.model_name].sudo().browse(doc_ids)
        return self.report_id.render_mrt_template_data(self, records[0], output_type=kwargs.get('output_type', 'pdf'))

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

    def _get_context(self):
        context = dict(super()._get_context() or {})
        context.update({
            'gc_si_key': self.env['instance.parameter'].sudo().get_param('gc.stimulsoft.key', '')
        })
        return context

    def _html_to_text(self, html_value):
        # Removing <br> with \n
        html_value = str(html_value or '').replace("<br>", "\n")
        # and removing all HTML tags
        return re.sub(r'<[^<]+?>', '', html_value)

    def _get_terms_and_condition_for_document(self, record):
        if record and 'terms_ids' in record:
            if record.terms_ids:
                terms = record.terms_ids.filtered(lambda t: t.document_type_id in self.document_type_id)
                if terms:
                    return self._html_to_text(terms[0].terms_and_conditions)
        return ''


class StimulReportMRTReportProduct(models.Model):
    _name = 'stimulsoft.mrt.report.product'
    _description = 'MRT Product Template'
    _order = 'sequence'

    report_id = fields.Many2one('stimulsoft.mrt.report', required=True, ondelete='cascade')
    product_id = fields.Many2one('freight.product', required=True)
    json_spec_id = fields.Many2one('product.json.specification', required=True)
    sequence = fields.Integer(default=0)
    mrt_file = fields.Binary(string='Template (.mrt)')
    filename = fields.Char(string='Filename')

    def _is_matched(self, records):
        domain = []
        if self.product_id and self.product_id.match_domain:
            domain = ast.literal_eval(self.product_id.match_domain or [])
        if not domain:
            domain = self.json_spec_id.get_product_domain()
        domain += [('id', 'in', records.ids)]
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
