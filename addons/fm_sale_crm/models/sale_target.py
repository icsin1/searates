
import json

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CRMSaleTarget(models.Model):
    _name = "crm.sale.target"
    _description = "Sale Target"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date_from desc, date_to desc"

    @api.model
    def get_default_weight_uom(self):
        return self.env.company.weight_uom_id.id

    @api.model
    def get_default_volume_uom(self):
        return self.env.company.volume_uom_id.id

    @api.depends('target_parameter')
    def _compute_non_fcl_target_parameter(self):
        for target in self:
            target.non_fcl_target_parameter = target.target_parameter if target.target_parameter != 'teu' else False

    @api.onchange('non_fcl_target_parameter')
    def _inverse_non_fcl_target_parameter(self):
        # Keep inverse and onchange both. Onchange:UI-update Inverse:Code-update
        for target in self:
            target.target_parameter = target.non_fcl_target_parameter if target.non_fcl_target_parameter else target.target_parameter

    def _get_target_parameter(self):
        return [
            ('weight', 'Weight'),
            ('volume', 'Volume'),
            ('gross_revenue', 'Gross Revenue'),
            ('gross_margin', 'Gross Margin'),
        ]

    def _get_non_fcl_target_parameter(self):
        parameter = self._get_target_parameter()
        parameter.append(('teu', 'TEUs'))
        return parameter

    @api.depends('transport_mode_id')
    def _compute_cargo_type_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.cargo_type_domain = json.dumps(domain)

    cargo_type_domain = fields.Char(compute='_compute_cargo_type_domain', store=True)

    name = fields.Char("Target Title", required=True)
    user_id = fields.Many2one("res.users", string="Sales Agent", required=True)
    manager_id = fields.Many2one("res.users", string="Reporting Manager")
    date_from = fields.Date("Target Date From", required=True)
    date_to = fields.Date("Target Date To", required=True)
    transport_mode_id = fields.Many2one("transport.mode", string="Transport Mode")
    shipment_type_id = fields.Many2one("shipment.type", string="Shipment Type")
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    cargo_type_id = fields.Many2one(
        'cargo.type', string='Cargo Type')
    is_package_group = fields.Boolean(related="cargo_type_id.is_package_group", store=True)
    # target_parameter field to use when needed in code/flow
    target_parameter = fields.Selection(_get_non_fcl_target_parameter, string="Target Parameter", required=True, tracking=True)
    # non_fcl_target_parameter field will be visible only when target is of FCL/Based on Package-group
    non_fcl_target_parameter = fields.Selection(_get_target_parameter, compute='_compute_non_fcl_target_parameter', inverse='_inverse_non_fcl_target_parameter')
    target_value = fields.Float(tracking=True)
    target_weight_uom_id = fields.Many2one(
        'uom.uom', string='Weight UoM', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom,
        tracking=True)
    target_volume_uom_id = fields.Many2one(
        'uom.uom', string="Volume UOM", domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)], default=get_default_volume_uom,
        tracking=True)
    target_currency_id = fields.Many2one("res.currency", string="Target Currency",
                                         default=lambda self: self.env.company.currency_id, tracking=True)
    incentive_type = fields.Selection([
        ('amount', 'Amount'),
        ('percentage', 'Percentage')
    ], string="Incentive")
    incentive_currency_id = fields.Many2one("res.currency", string="Incentive Currency",
                                            default=lambda self: self.env.company.currency_id)
    incentive_unit = fields.Float()
    incentive_unit_type = fields.Selection([
        ('net', 'NET PROFIT'),
        ('gross', 'GROSS REVENUE'),
        ('freight', 'FREIGHT AMOUNT')
    ])
    remarks = fields.Text()
    sale_target_line_ids = fields.One2many('crm.sale.target.line', 'sale_target_id', string="Lines")
    is_fields_mandatory = fields.Boolean('Target Mandatory Fields')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Target Name must be unique!'),
        ('target_dates_check', "CHECK ((date_from <= date_to))", "The Target Date From must be before the Target Date To.")
    ]

    @api.constrains('target_value')
    def _check_default_target_value(self):
        for rec in self:
            if rec.target_value <= 0:
                raise ValidationError(_('The target value must be greater than 0.'))

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        for target in self:
            target.cargo_type_id = False

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = _("%s (copy)") % (self.name or '')
        return super(CRMSaleTarget, self).copy(default)

    def get_dates(self, start_date, end_date):
        while True:
            next_start = start_date + relativedelta(months=1, day=1)
            this_end = next_start - relativedelta(days=1)

            if end_date <= this_end:
                yield start_date, end_date
                break

            yield start_date, this_end
            start_date = next_start

    def action_generate_monthly_target(self):
        for target in self:
            target_date_range = list(self.get_dates(target.date_from, target.date_to))
            sale_target_line_vals = [(5, 0)]
            if target_date_range:
                monthly_target_value = target.target_value / len(target_date_range)
                target_uom_id = False
                target_currency_id = False
                if target.target_parameter == "weight":
                    target_uom_id = target.target_weight_uom_id.id
                elif target.target_parameter == "volume":
                    target_uom_id = target.target_volume_uom_id.id
                elif target.target_parameter in ["gross_revenue", "gross_margin"]:
                    target_currency_id = target.target_currency_id.id
                for date_range in target_date_range:
                    sale_target_line_vals.append((0, 0, {
                        'target_parameter': target.target_parameter,
                        'target_value': monthly_target_value,
                        'target_uom_id': target_uom_id,
                        'date_from': date_range[0],
                        'date_to': date_range[1],
                        'target_currency_id': target_currency_id,
                    }))
            if sale_target_line_vals:
                target.write({
                    'sale_target_line_ids': sale_target_line_vals,
                })

    def _cron_generate_monthly_target(self):
        self.search([]).action_recompute_actual_values()

    def action_recompute_actual_values(self):
        for target in self:
            target.sale_target_line_ids._compute_actual_value()

    def get_excel_report_field_name(self):
        return ['period', 'house_shipment_names', 'target_parameter', 'target_value', 'target_uom_id', 'actual_value']

    def action_download(self):
        field_names = self.get_excel_report_field_name()
        if self.target_parameter not in ['weight', 'volume']:
            field_names.remove('target_uom_id')
        data = json.dumps({
                'field_names': field_names,
                'model': self.sale_target_line_ids._name,
                'ids': self.sale_target_line_ids.ids,
                'domain': [],
                'import_compat': False,
                'context': self._context,
                })

        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': f'/odoo_web/export/xlsx/?data={data}',
        }

    @api.model
    def default_get(self, fields):
        defaults = super(CRMSaleTarget, self).default_get(fields)
        defaults['is_fields_mandatory'] = self.env['ir.config_parameter'].sudo().get_param('fm_sale_crm.target_mandatory_fields', False)
        return defaults

    @api.model_create_single
    def create(self, values):
        res = super().create(values)
        res.action_generate_monthly_target()
        return res
