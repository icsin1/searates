
from odoo import models, fields


class CRMSaleTargetLine(models.Model):
    _inherit = "crm.sale.target.line"

    target_parameter = fields.Selection(selection_add=[('quotation', 'Quotation')], ondelete={'quotation': 'cascade'})
    shipment_quotation_name = fields.Char(compute='_compute_shipment_quotation_name', string='Quotation Number')

    def _compute_shipment_quotation_name(self):
        shipment_quote_obj = self.env['shipment.quote']
        for line in self:
            line.shipment_quotation_name = ', '.join(shipment_quote_obj.search(line.get_shipment_quote_actual_value_domain()).mapped('name'))

    def _compute_actual_value(self):
        super()._compute_actual_value()
        shipment_quote_obj = self.env['shipment.quote']
        for line in self:
            if line.target_parameter == 'quotation':
                line.actual_value = shipment_quote_obj.search_count(line.get_shipment_quote_actual_value_domain())

    def get_shipment_quote_actual_value_domain(self):
        self.ensure_one()
        domain = [
            ('company_id', '=', self.sale_target_id.company_id.id),
            ('state', '=', 'accept'),
            ('user_id', '=', self.user_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)]
        if self.sale_target_id.shipment_type_id:
            domain += [('shipment_type_id', '=', self.sale_target_id.shipment_type_id.id)]
        if self.sale_target_id.transport_mode_id:
            domain += [('transport_mode_id', '=', self.sale_target_id.transport_mode_id.id)]
        if self.sale_target_id.cargo_type_id:
            domain += [('cargo_type_id', '=', self.sale_target_id.cargo_type_id.id)]
        return domain
