# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    quote_approver_id = fields.Many2one('res.users', string="Default Quote Approver", default=lambda self: self.env.ref('base.user_admin'))
    quote_sale_agent_id = fields.Many2one('res.users', string="Default Quote Sale Agent", default=lambda self: self.env.ref('base.user_admin'))
