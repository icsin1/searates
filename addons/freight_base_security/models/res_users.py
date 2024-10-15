# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_approval_authority = fields.Boolean(copy=False, inverse='_inverse_approval_authority')
    approver_id = fields.Many2one(
        'res.users', string='Manager/Document Approver', domain=lambda self: "[('groups_id', '=', {})]".format(
            self.env.ref('freight_base.group_user_freight_approver_team', raise_if_not_found=False).id
        ), copy=False)
    user_role_id = fields.Many2one('res.user.role', string='Department')
    login = fields.Char(required=True, help="Used to log into the system", string="Email Address")
    company_id = fields.Many2one('res.company', string='Default Company', required=True, default=lambda self: self.env.company.id,
                                 help='The default company for this user.', context={'user_preference': True})
    company_ids = fields.Many2many('res.company', 'res_company_users_rel', 'user_id', 'cid',
                                   string='Allowed Companies', default=lambda self: self.env.company.ids)

    @api.depends('groups_id', 'is_approval_authority')
    def _inverse_approval_authority(self):
        for user in self:
            if user.is_approval_authority:
                user.groups_id = [(4, self.env.ref('freight_base.group_user_freight_approver_team', raise_if_not_found=False).id)]
            else:
                user.groups_id = [(3, self.env.ref('freight_base.group_user_freight_approver_team', raise_if_not_found=False).id)]

    def action_create_role(self):
        self = self.sudo()
        self.env['res.user.role'].create({
            'name': 'Role from %s' % self.name,
            'groups_id':  [(6, 0, self.groups_id.ids)]
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Message'),
            'res_model': 'message.dialog',
            'view_mode': 'form',
            'target': 'new',
            'views': [[self.env.ref('freight_base_security.action_message_dialog_form').id, 'form']]
        }

    @api.model
    def create(self, vals):
        if 'login' in vals and vals.get('login'):
            login = str(vals['login']).lower()
            vals.update({'login': login.strip()})
        res = super().create(vals)
        if 'user_role_id' in vals:
            res.groups_id = res.user_role_id.groups_id
        return res

    def write(self, vals):
        if 'login' in vals and vals.get('login'):
            login = str(vals['login']).lower()
            vals.update({'login': login.strip()})
        res = super().write(vals)
        if 'user_role_id' in vals and 'groups_id' not in vals:
            for user in self:
                user.groups_id = user.user_role_id.groups_id
        return res

    @api.model
    def _get_login_domain(self, login):
        login = str(login).lower().strip()
        return super(ResUsers, self)._get_login_domain(login)
