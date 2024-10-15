from odoo import models


class ShipmentChargeProFormaInvoiceWizardLine(models.TransientModel):
    _inherit = 'shipment.charge.pro.forma.invoice.wizard.line'

    def _prepare_pro_forma_invoice_line(self):
        charge_lines = super()._prepare_pro_forma_invoice_line()
        house_shipment_charge_revenue_obj = self.env['house.shipment.charge.revenue']
        for charge_line in charge_lines:
            charge_id = house_shipment_charge_revenue_obj.browse(charge_line[2]['house_shipment_charge_revenue_id'])
            if charge_id:
                charge_line[2]['income_tds_rate_id'] = charge_id.income_tds_rate_id.id
        return charge_lines
