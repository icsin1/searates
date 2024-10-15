from odoo import models


class IrActionsActions(models.Model):
    _inherit = 'ir.actions.actions'

    def _get_readable_fields(self):
        readable_fields = super()._get_readable_fields()
        if 'report_res_model' in self._fields:
            readable_fields = set(list(readable_fields) + ['report_res_model', 'report_res_id'])
        return readable_fields
