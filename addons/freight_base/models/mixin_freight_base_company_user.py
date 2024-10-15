from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightBaseCompanyUserMixin(models.AbstractModel):
    _name = 'freight.base.company.user.mixin'
    _description = 'Freight Company-User Mixin'

    # Base Company & User Details
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    country_id = fields.Many2one('res.country', related='company_id.country_id', store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    user_id = fields.Many2one('res.users', string="Responsible", required=True, default=lambda self: self.env.user, domain="[('company_id', '=', company_id)]")
