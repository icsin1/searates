from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import Action


class WebAction(Action):

    def _get_action_id(self, action_id):
        try:
            action_id = int(action_id)
        except ValueError:
            try:
                action = request.env.ref(action_id)
                assert action._name.startswith('ir.actions.')
                action_id = action.id
            except Exception:
                action_id = 0   # force failed read
        return action_id

    @http.route()
    def load(self, action_id, additional_context=None):
        """ Overriding method to add additional model and report related information in action values
        """
        values = super().load(action_id, additional_context=additional_context)
        if 'report_type' in values and values.get('report_type') != 'qweb-pdf':
            Actions = request.env['ir.actions.actions']
            action_id = self._get_action_id(action_id)
            base_action = Actions.browse([action_id]).sudo().read(['type'])
            if base_action:
                ctx = dict(request.context)
                action_type = base_action[0]['type']
                if action_type == 'ir.actions.report':
                    ctx.update({'bin_size': True})
                if additional_context:
                    ctx.update(additional_context)
                request.context = ctx
                action = request.env[action_type].sudo().browse([action_id])
                values.update({
                    'report_res_model': action.report_res_model,
                    'report_res_id': action.report_res_id
                })
        return values
