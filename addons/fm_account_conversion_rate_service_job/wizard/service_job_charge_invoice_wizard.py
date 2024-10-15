from odoo import models


class ServiceJobChargeInvoiceWizardLine(models.TransientModel):
    _inherit = 'service.job.charge.invoice.wizard.line'

    def _generate_invoice(self, move_type):
        invoice_vals = super()._generate_invoice(move_type)
        if not self.charge_ids:
            return invoice_vals
        charge_id = self.charge_ids[0]
        invoice_vals['currency_exchange_rate'] = self.wizard_id.get_exchange_rate(charge_id)
        return invoice_vals

    def _prepare_invoice_line(self, move_type):
        invoice_lines = super()._prepare_invoice_line(move_type)
        service_job_charge_cost_obj = self.env['service.job.charge.revenue']
        wizard = self.wizard_id
        for invoice_line in invoice_lines:
            charge_id = service_job_charge_cost_obj.browse(invoice_line[2].get('service_job_charge_revenue_id'))
            currency_exchange_rate = wizard.get_exchange_rate(charge_id)
            charge_rate = charge_id.amount_currency_id.with_context(
                currency_exchange_rate=currency_exchange_rate)._convert(
                charge_id.amount_rate, self.currency_id, charge_id.service_job_id.company_id, charge_id.service_job_id.date, round=False)
            line_currency_exchange_rate = wizard.get_invoice_bill_line_exchange_rate(charge_id)

            invoice_line[2].update({
                'currency_exchange_rate': line_currency_exchange_rate,
                'charge_rate_per_unit': charge_id.amount_rate,
                'price_unit': charge_rate
                })
        return invoice_lines
