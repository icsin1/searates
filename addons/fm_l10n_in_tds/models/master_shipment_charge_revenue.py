from odoo import models, fields, api


class MasterShipmentChargeRevenue(models.Model):
    _inherit = 'master.shipment.charge.revenue'

    income_tds_rate_id = fields.Many2one('account.tds.rate', string="Income TDS Rate", copy=False)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super()._onchange_product_id()
        product = self.product_id
        if product and self.company_calculate_tds:
            self.income_tds_rate_id = product.income_tds_rate_id.id
