from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShipmentChargeBillWizardLine(models.TransientModel):
    _inherit = 'master.shipment.charge.bill.wizard.line'

    def _generate_invoice(self, move_type):
        invoice_vals = super()._generate_invoice(move_type)
        if not self.charge_ids:
            return invoice_vals
        charge_id = self.charge_ids[0]
        invoice_vals['currency_exchange_rate'] = self.wizard_id.get_exchange_rate(charge_id)
        return invoice_vals

    def _prepare_invoice_line(self, move_type):
        self.ensure_one()
        cost_invoice_lines = super()._prepare_invoice_line(move_type)
        master_shipment_charge_cost_obj = self.env['master.shipment.charge.cost']
        wizard = self.wizard_id
        for invoice_line in cost_invoice_lines:
            charge_id = master_shipment_charge_cost_obj.browse(invoice_line[2].get('master_shipment_charge_cost_id'))
            currency_exchange_rate = wizard.get_exchange_rate(charge_id)
            charge_rate = charge_id.amount_currency_id\
                .with_context(currency_exchange_rate=currency_exchange_rate)._convert(
                charge_id.amount_rate, self.currency_id, charge_id.master_shipment_id.company_id,
                charge_id.master_shipment_id.shipment_date)
            line_currency_exchange_rate = wizard.get_invoice_bill_line_exchange_rate(charge_id)

            invoice_line[2].update({
                'currency_exchange_rate': line_currency_exchange_rate,
                'charge_rate_per_unit': charge_id.amount_rate,
                'price_unit': charge_rate
            })
        return cost_invoice_lines
