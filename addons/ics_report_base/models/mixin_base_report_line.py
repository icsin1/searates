from odoo import models, fields


class BaseReportLine(models.AbstractModel):
    _name = 'mixin.base.report.line'
    _description = 'Base Report Line/Section'
    _order = 'sequence,hierarchy_level,name'

    name = fields.Char(required=True, string='Report Line')
    foldable = fields.Boolean(default=False)
    active = fields.Boolean(default=True)

    # Default Section Filter Domain
    default_action_domain = fields.Text(default='[]', string='Default Action Domain')

    # Properties
    code = fields.Char()
    action_id = fields.Many2one('ir.actions.actions', string='Action', help='If set, user will be redirected to action')
    hierarchy_level = fields.Integer(default=1)  # FIXME: This will be auto calculated based on parent defined
    group_total = fields.Boolean(default=True)

    group_by_fields = fields.Char(string='Group By', help='Group by Different fields to create hierarchy left to right, comma separated')
    hide_if_zero = fields.Boolean(default=False)
    sequence = fields.Integer(default=0)
