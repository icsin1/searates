from odoo import models, fields, api


class BaseReportFilter(models.AbstractModel):
    _name = 'mixin.base.report.filter'
    _description = 'Base Report Filter'
    _order = 'sequence,name'

    name = fields.Char(required=True, string='Filter Name')
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade')
    ir_model_field_id = fields.Many2one('ir.model.fields', domain="[('ttype', 'in', ['many2one']), ('model_id', '=', model_id)]", ondelete='cascade', string='Field')
    field_model_name = fields.Char(compute='_compute_model_name', store=True)
    data_domain = fields.Text(default='[]', required=True)
    sequence = fields.Integer(default=0)

    @api.depends('ir_model_field_id')
    def _compute_model_name(self):
        for rec in self:
            if rec.ir_model_field_id.ttype in ('many2one', 'many2many', 'one2many'):
                rec.field_model_name = rec.ir_model_field_id.relation
            else:
                rec.field_model_name = False
