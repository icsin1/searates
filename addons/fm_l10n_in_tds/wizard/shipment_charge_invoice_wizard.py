
from odoo import models


class ShipmentChargeInvoiceWizard(models.TransientModel):
    _inherit = 'shipment.charge.invoice.wizard'

    def action_view_invoice(self, invoices, move_type):
        action = super().action_view_invoice(invoices, move_type)
        for invoice in invoices:
            invoice._onchange_total_tds_amount()
        return action


class ShipmentChargeInvoiceWizardLine(models.TransientModel):
    _inherit = 'shipment.charge.invoice.wizard.line'

    def _prepare_invoice_line(self, move_type):
        revenue_invoice_lines = super()._prepare_invoice_line(move_type)
        house_shipment_charge_revenue_obj = self.env['house.shipment.charge.revenue']
        for invoice_line in revenue_invoice_lines:
            charge_id = house_shipment_charge_revenue_obj.browse(invoice_line[2].get('house_shipment_charge_revenue_id'))
            if charge_id and charge_id.company_calculate_tds:
                invoice_line[2]['account_tds_rate_id'] = charge_id.income_tds_rate_id.id
        return revenue_invoice_lines
