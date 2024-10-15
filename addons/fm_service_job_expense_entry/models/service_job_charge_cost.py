from odoo import models, _
from odoo.exceptions import UserError


class ServiceJobChargeCost(models.Model):
    _inherit = 'service.job.charge.cost'

    def action_create_expense_entry(self):
        charges_to_bill = self.filtered(lambda line: line.status in ('no'))  # Only full amount can be created as Journal Expense Entry
        if not charges_to_bill:
            raise UserError(_("Nothing to register."))
        self_partner = self.mapped('company_id')[0].partner_id
        if charges_to_bill.filtered(lambda charge: charge.partner_id != self_partner):
            raise UserError(_('You can not create expense entry other then your Company as Creditor'))

        self.check_charges_rate_per_unit('vendor bill')
        action = self.env.ref('fm_service_job_expense_entry.service_freight_job_expense_entry_wizard_action').sudo().read([])[0]
        action['context'] = {
            'default_charge_ids': [(6, False, charges_to_bill.ids)],
            'default_company_id': self.company_id.id,
            'default_currency_id': self.company_id.currency_id.id,
            'default_service_job_id': charges_to_bill[0].service_job_id.id
        }
        return action

    def _get_action_for_view_moves(self):
        action, move_type = super()._get_action_for_view_moves()

        if 'entry' in self.move_line_ids.mapped('move_id.move_type'):
            move_type = 'entry'
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
            action['context'] = {'default_service_job_id': self.id, 'default_move_type': 'entry', 'create': 0, 'search_default_posted': 1}

        return action, move_type
