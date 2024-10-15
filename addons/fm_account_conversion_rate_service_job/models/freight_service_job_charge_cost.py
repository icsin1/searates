from itertools import groupby

from odoo import models, _
from odoo.exceptions import ValidationError


class FreightServiceChargeCost(models.Model):
    _inherit = 'service.job.charge.cost'

    def action_create_vendor_bill(self):
        self.check_currency_conversion_rate()
        return super().action_create_vendor_bill()

    def check_currency_conversion_rate(self):
        """ Validating all the currency rate are same for the bill lines
        """
        service_job_charge_cost_obj = self.env['service.job.charge.cost']
        other_currency_to_invoice = self.filtered(lambda l: l.amount_currency_id != l.currency_id)

        for currency_id, service_job_charges in groupby(other_currency_to_invoice, lambda m: m.amount_currency_id):
            service_job_charges = service_job_charge_cost_obj.concat(*service_job_charges)
            service_job_charges_name = ", ".join(charge.charge_description for charge in service_job_charges)
            if len(set(service_job_charges.mapped('amount_conversion_rate'))) > 1:
                raise ValidationError(_("Exchange rate must be same for %s charges.") % (service_job_charges_name))
        return
