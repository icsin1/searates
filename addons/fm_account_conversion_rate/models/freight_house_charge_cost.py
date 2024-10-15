from itertools import groupby

from odoo import models, _
from odoo.exceptions import ValidationError


class HouseShipmentChargeCost(models.Model):
    _inherit = 'house.shipment.charge.cost'

    def action_create_vendor_bill(self):
        self.check_currency_conversion_rate()
        return super().action_create_vendor_bill()

    def check_currency_conversion_rate(self):
        """ Validating all the currency rate are same for the bill lines
        """
        house_shipment_charge_cost_obj = self.env['house.shipment.charge.cost']
        other_currency_to_invoice = self.filtered(lambda l: l.amount_currency_id != l.currency_id)

        for currency_id, house_shipment_charges in groupby(other_currency_to_invoice, lambda m: m.amount_currency_id):
            house_shipment_charges = house_shipment_charge_cost_obj.concat(*house_shipment_charges)
            house_shipment_charges_name = ", ".join(charge.charge_description for charge in house_shipment_charges)
            if len(set(house_shipment_charges.mapped('amount_conversion_rate'))) > 1:
                raise ValidationError(_("Exchange rate must be same for %s charges.") % (house_shipment_charges_name))
        return
