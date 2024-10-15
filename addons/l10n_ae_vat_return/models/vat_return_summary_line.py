from odoo import models, fields


class VATReturnSummaryLine(models.Model):
    _name = "vat.return.summary.line"
    _description = "vat.return.summary.line"

    vat_return_id = fields.Many2one('vat.return', string='Vat Return ID')
    description = fields.Char('Description')
    box_no = fields.Char('Box')
    base_amount = fields.Float('Base Amount', default=0.0)
    tax_amount = fields.Float('Tax Amount', default=0.0)
    adjustment_amount = fields.Float('Adjustment Amount', default=0.0)
