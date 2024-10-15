# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    quote_approver_id = fields.Many2one('res.users', string='Default Quote Approver', readonly=False, related='company_id.quote_approver_id')
    quote_sale_agent_id = fields.Many2one('res.users', string="Default Quote Sale Agent", readonly=False, related='company_id.quote_sale_agent_id')