from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import DataSet


class CustomDataSet(DataSet):

    @http.route(['/web/dataset/call_kw', '/web/dataset/call_kw/<path:path>'], type='json', auth="user")
    def call_kw(self, model, method, args, kwargs, path=None):
        if kwargs.get('active_model') != model:
            action_id = request.env['ir.actions.act_window'].sudo().search([
                '&', ('res_model', '=', model), ('res_model', '!=', 'ir.audit.log.action')
            ], limit=1)
            params = kwargs.get('context', {}).get('params', {})
            menu_obj = False
            if params and params.get('menu_id') and isinstance(params.get('menu_id'), int):
                menu_obj = request.env['ir.ui.menu'].browse([int(params.get('menu_id'))])
            if action_id and menu_obj and request.uid and (request.env.is_admin() or not request.env.user.active):
                request.env['ir.audit.log.action'].sudo().create({
                    'action_id': action_id.id,
                    'action_dump': str(params),
                    'user_id': request.uid,
                    'menu_id': menu_obj.id,
                    'company_id': request.env.company.id
                })
        return self._call_kw(model, method, args, kwargs)
