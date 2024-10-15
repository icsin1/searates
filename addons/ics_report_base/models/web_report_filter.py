from slugify import slugify
from odoo import models, fields, api, _


class WebReportFilter(models.Model):
    _name = 'web.report.filter'
    _inherit = 'mixin.base.report.filter'
    _description = 'Web Report Filter'

    web_report_id = fields.Many2one('web.report', required=True, ondelete='cascade')
    model_id = fields.Many2one('ir.model', related='web_report_id.model_id', store=True)
    filter_type = fields.Selection([
        ('single_relation', 'Single Record'),
        ('multi_relation', 'Multiple Record'),
        ('input', 'User Input'),
        ('choice', 'Choice'),
        ('choice_multi', 'Multi Choice'),
    ], default='single_relation', required=True)
    filter_key = fields.Char(required=True, string='Filter Key')
    choice_ids = fields.One2many('web.report.filter.choice', 'filter_id', string='Choices')
    icon = fields.Char(required=True, default='fa-filter', string='Icon')
    default_value = fields.Char(string='Default Value')

    _sql_constraints = [
        (
            "unique_filter_key",
            "unique(unique_import_id)",
            "A filter Key must be unique!",
        )
    ]

    @api.onchange('name')
    def _onchange_name(self):
        self.filter_key = 'filter_{}'.format(slugify(self.name or '', separator='_')) if (not self.filter_key or self.filter_key == 'filter_') else self.filter_key

    def get_name(self, option_value):
        self.ensure_one()
        if self.filter_type == 'input':
            return '{} {}'.format(option_value or self.default_value, self.name)
        elif self.filter_type in ['choice', 'choice_multi']:
            default_choice = self.choice_ids.filtered(lambda choice: option_value and (choice.choice_key == option_value or choice.choice_key in option_value))
            if not default_choice:
                default_choice = self.choice_ids.filtered(lambda choice: choice.is_default)
            if sorted(self.choice_ids.mapped('choice_key')) == sorted(option_value or []) or isinstance(option_value, list) and not option_value:
                choice_names = _('All')
            else:
                choice_names = ','.join(default_choice.mapped('name'))
            return '{} {}'.format(self.name, default_choice and choice_names or 'None')
        return self.name

    def get_default_value(self):
        self.ensure_one()
        if self.filter_type in ['choice', 'choice_multi']:
            default_choice = self.choice_ids.filtered(lambda choice: choice.is_default)
            return default_choice.mapped('choice_key') or []
        return self.default_value


class WebReportFilterChoice(models.Model):
    _name = 'web.report.filter.choice'
    _description = 'Filter Choice'
    _order = 'sequence'

    filter_id = fields.Many2one('web.report.filter', required=True, ondelete='cascade')
    name = fields.Char(required=True, string='Choice Label')
    choice_key = fields.Char(required=True, string='Choice Key')
    is_default = fields.Boolean(default=False, required=True, string='Default')
    sequence = fields.Integer(default=10, required=True)

    _sql_constraints = [
        (
            "unique_filter_choice_key",
            "unique(filter_id,choice_key)",
            "A filter choice key must be unique!",
        )
    ]
