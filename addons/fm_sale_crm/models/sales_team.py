# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmProspectTeam(models.Model):
    _name = "crm.prospect.team"
    _inherit = ['mail.thread']
    _description = "Sales Team"
    _order = "sequence ASC, create_date DESC, id DESC"
    _check_company_auto = True

    def _get_user_domain(self):
        return [('share', '=', False), ('groups_id', '=', self.env.ref('fm_sale_crm.group_sales_manager').id)]

    def _get_member_domain(self):
        return [('share', '=', False), ('groups_id', '=', self.env.ref('fm_sale_crm.group_salesman').id)]

    name = fields.Char('Sales Team', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True, help="If the active field is set to false"
                                               ", it will allow you to hide the Sales Team without removing it.")
    company_id = fields.Many2one(
        'res.company', string='Company', index=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        "res.currency", string="Currency",
        related='company_id.currency_id', readonly=True)
    user_id = fields.Many2one('res.users', string='Team Leader', check_company=True, domain=_get_user_domain)
    member_ids = fields.Many2many(
        'res.users', string='Salespersons', copy=False,
        help="Users assigned to this team.", domain=_get_member_domain)

    @api.constrains('member_ids')
    def _check_member_ids(self):
        multi_enabled = self.env['ir.config_parameter'].sudo().get_param('fm_sale_crm.membership_multi', False)
        if not multi_enabled:
            current_member_ids = self.member_ids.ids
            other_teams = self.search([]) - self
            if other_teams:
                other_team_member_ids = other_teams.member_ids.ids
                current_member_ids = set(current_member_ids)
                other_team_member_ids = set(other_team_member_ids)
                if current_member_ids & other_team_member_ids:
                    raise UserError(_('Enable Multi Teams in Settings to add Same Salesperson in Multiple Teams'))
