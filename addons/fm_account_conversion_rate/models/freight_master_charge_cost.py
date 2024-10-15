from itertools import groupby

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MasterShipmentChargeCost(models.Model):
    _inherit = 'master.shipment.charge.cost'

    def action_create_vendor_bill(self):
        self.check_currency_conversion_rate()
        return super().action_create_vendor_bill()

    def check_currency_conversion_rate(self):
        """ Validating all the currency rate are same for the bill lines
        """
        master_shipment_charge_cost_obj = self.env['master.shipment.charge.cost']
        other_currency_to_invoice = self.filtered(lambda l: l.amount_currency_id != l.currency_id)

        for currency_id, master_shipment_charges in groupby(other_currency_to_invoice, lambda m: m.amount_currency_id):
            master_shipment_charges = master_shipment_charge_cost_obj.concat(*master_shipment_charges)
            master_shipment_charges_name = ", ".join(charge.charge_description for charge in master_shipment_charges)
            if len(set(master_shipment_charges.mapped('amount_conversion_rate'))) > 1:
                raise ValidationError(_("Exchange rate must be same for %s charges.") % (master_shipment_charges_name))
        return
