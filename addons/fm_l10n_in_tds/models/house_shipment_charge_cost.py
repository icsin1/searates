from odoo import models, fields, api


class HouseShipmentChargeCost(models.Model):
    _inherit = 'house.shipment.charge.cost'

    expense_tds_rate_id = fields.Many2one('account.tds.rate', string="Expense TDS Rate", copy=False)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super()._onchange_product_id()
        product = self.product_id
        if product and self.company_calculate_tds:
            self.expense_tds_rate_id = product.expense_tds_rate_id.id
