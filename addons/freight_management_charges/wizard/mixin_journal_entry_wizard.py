from odoo import models, fields, api


class JournalEntryGenerateWizardMixin(models.AbstractModel):
    _name = 'journal.entry.generate.wizard.mixin'
    _description = 'Journal Entry Generate Wizard Mixin'

    billing_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill')
    ], default='out_invoice', required=True)
    partner_mode = fields.Selection([
        ('all', 'All'),
        ('specific', 'Specific')
    ], default='all', required=True)
    partner_ids = fields.Many2many('res.partner', string='Partners')
    single_currency_billing = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', string='Invoice Currency')
    amount_conversion_rate = fields.Float(string='Exchange Rate', default=1, required=True, digits='Currency Exchange Rate')


class JournalEntryGenerateWizardLineMixin(models.AbstractModel):
    _name = 'journal.entry.generate.wizard.line.mixin'
    _description = 'Journal Entry Generate Wizard Line Mixin'

    partner_id = fields.Many2one('res.partner', string='Partner')
    currency_id = fields.Many2one('res.currency', string="Currency")
    no_of_charges = fields.Integer(string='No. Of Charges')
    amount = fields.Monetary(string='Total Amount')
    full_amount = fields.Monetary(string='Full Amount')
    is_partial_invoice = fields.Boolean(compute='_compute_is_partial_invoice', store=True)

    @api.depends('amount', 'full_amount')
    def _compute_is_partial_invoice(self):
        for rec in self:
            rec.is_partial_invoice = rec.amount != rec.full_amount
