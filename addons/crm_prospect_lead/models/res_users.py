from odoo import api, models, SUPERUSER_ID


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        # If you want to remove this then please check commit first
        if self._context and self._context.get('access_all_team_member') and self._context.get('team_id'):
            team_id = self.env['crm.prospect.team'].sudo().browse(self._context.get('team_id'))
            allowed_user_ids = team_id.member_ids.ids
            allowed_user_ids.append(team_id.user_id.id)
            args = [('id', 'in', allowed_user_ids)]
            name_get_uid = SUPERUSER_ID
        return super()._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        # This method is written to get records on click of search more from drop down also
        if self._context and self._context.get('access_all_team_member') and self._context.get('team_id'):
            team_id = self.env['crm.prospect.team'].sudo().browse(self._context.get('team_id'))
            allowed_user_ids = team_id.member_ids.ids
            allowed_user_ids.append(team_id.user_id.id)
            domain = [('id', 'in', allowed_user_ids)]
        return super().search_read(domain, fields, offset, limit, order)
