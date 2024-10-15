# -*- coding: utf-8 -*-

from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_crm_prospect_lead(self):
        user_id = self.env.user.id
        sales_teams = self.env['crm.prospect.team'].search([('user_id', '=', user_id)]).mapped('member_ids').ids
        allowed_users = [user_id] + sales_teams
        lead_ids = self.env['crm.prospect.lead'].search([('user_id', 'in', allowed_users)])
        return [('id', 'in', lead_ids.ids)]

    def get_crm_prospect_opportunity(self):
        user_id = self.env.user.id
        sales_teams = self.env['crm.prospect.team'].search([('user_id', '=', user_id)]).mapped('member_ids').ids
        allowed_users = [user_id] + sales_teams
        opportunity_ids = self.env['crm.prospect.opportunity'].search([('user_id', 'in', allowed_users)])
        return [('id', 'in', opportunity_ids.ids)]

    def get_shipment_quote(self):
        user_id = self.env.user.id
        sales_teams = self.env['crm.prospect.team'].search([('user_id', '=', user_id)]).mapped('member_ids').ids
        allowed_users = [user_id] + sales_teams
        quote_ids = self.env['shipment.quote'].search([('user_id', 'in', allowed_users)])
        return [('id', 'in', quote_ids.ids)]
