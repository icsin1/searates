# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.portal.controllers import portal


class PortalAccountDashboard(portal.CustomerPortal):

    def _prepare_account_domain(self, partner):
        return [('move_type', '=', 'out_invoice'), ('partner_id', '=', partner.id), ('state', 'not in', ['draft', 'cancel'])]

    def _prepare_home_portal_values(self, counters):
        values = super(PortalAccountDashboard, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        move_obj = request.env['account.move']
        move_ids = move_obj.search(self._prepare_account_domain(partner))
        move_paid_amount = 0
        move_due_amount = 0
        company_currency_name = request.env.user.company_id.currency_id.name
        if move_obj.check_access_rights('read', raise_exception=False):
            for move in move_ids:
                move_due_amount += move.amount_residual_signed
                move_paid_amount += (move.amount_total_signed - move.amount_residual_signed)
        if 'dashboard_account_total' in counters:
            values['dashboard_account_total'] = "%s %s" % (round(move_paid_amount, 2), company_currency_name)
        if 'dashboard_account_due_total' in counters:
            values['dashboard_account_due_total'] = "%s %s" % (round(move_due_amount, 2), company_currency_name)
        return values
