from odoo import models, fields, api


class ProFormaInvoice(models.Model):
    _inherit = 'pro.forma.invoice'

    company_calculate_tds = fields.Boolean(related='company_id.calculate_tds', store=True)
    total_tds_amount = fields.Monetary(string='Total TDS', store=True, readonly=True,
                                       tracking=True, compute='cal_total_tds_amount')

    @api.depends('pro_forma_invoice_line_ids', 'pro_forma_invoice_line_ids.tds_amount')
    def cal_total_tds_amount(self):
        for rec in self:
            rec.total_tds_amount = sum(rec.pro_forma_invoice_line_ids.mapped('tds_amount'))

    def _prepare_invoice_line(self):
        self.ensure_one()
        invoice_lines = super(ProFormaInvoice, self)._prepare_invoice_line()
        house_shipment_charge_revenue_obj = self.env['house.shipment.charge.revenue']
        for invoice_line in invoice_lines:
            charge_id = house_shipment_charge_revenue_obj.browse(invoice_line[2]['house_shipment_charge_revenue_id'])
            if charge_id:
                invoice_line[2].update({'account_tds_rate_id': charge_id.income_tds_rate_id.id})
        return invoice_lines


class ProFormaInvoiceLine(models.Model):
    _inherit = 'pro.forma.invoice.line'

    income_tds_rate_id = fields.Many2one('account.tds.rate', string="TDS Rate", copy=False)
    tds_amount = fields.Monetary(string='TDS Amount', store=True, compute='cal_income_tds_rate_amount', currency_field='company_currency_id')

    @api.depends('income_tds_rate_id', 'price_subtotal')
    def cal_income_tds_rate_amount(self):
        for rec in self:
            rec.tds_amount = (rec.income_tds_rate_id.rate_percentage * rec.price_subtotal) / 100
