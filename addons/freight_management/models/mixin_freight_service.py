# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightServiceMixin(models.AbstractModel):
    _name = 'freight.service.mixin'
    _description = 'Freight Service Mixin'

    def _default_creditor(self):
        creditor = self.env['res.partner'].search([('category_ids.is_vendor', '=', True)], limit=1)
        return creditor and creditor.id

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def get_charge_domain(self):
        self.ensure_one()
        charge_category = self.env.ref('freight_base.shipment_charge_category', raise_if_not_found=False)
        return json.dumps(['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False), ('categ_id', '=', charge_category.id)])

    @api.depends('company_id')
    def _compute_charge_domain(self):
        for service in self:
            service.charge_domain = service.get_charge_domain()

    sequence = fields.Integer(string='Sequence', default=10)
    charge_domain = fields.Char(compute='_compute_charge_domain')
    product_id = fields.Many2one('product.product', string='Charge Type', required=True, tracking=True)
    service_name = fields.Char(string='Charge Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Local Currency', tracking=True)
    uom_id = fields.Many2one('uom.uom', string='UoM', required=True, tracking=True)
    quantity = fields.Float(string='No of Units', default=1, required=True, tracking=True, digits='Product Unit of Measure')
    measurement_basis_id = fields.Many2one('freight.measurement.basis', string='Measurement Basis', required=True, tracking=True)
    # Container Type based Measurement Basis
    is_container_type_basis = fields.Boolean(compute='_compute_is_container_type_basis')
    container_type_id = fields.Many2one('freight.container.type', string='Container Type')

    # Cost
    cost_currency_id = fields.Many2one('res.currency', string='Cost Currency', required=True, tracking=True)
    cost_conversion_rate = fields.Float(string='Cost Exchange', default=1, tracking=True, digits=(16, 3))
    cost_amount_rate = fields.Monetary(string='Cost Rate per Unit', currency_field='cost_currency_id', tracking=True)
    creditor_partner_id = fields.Many2one('res.partner', string='Creditor', tracking=True, inverse='_inverse_creditor_partner')
    creditor_address_id = fields.Many2one('res.partner', string='Creditor Address', domain="['|', ('parent_id', '=', creditor_partner_id), ('id', '=', creditor_partner_id)]", tracking=True)
    cost_remarks = fields.Text(string='Cost Remarks', tracking=True)
    cost_currency_mismatch = fields.Boolean(compute='_compute_currency_mismatch', tracking=True)

    # Revenue
    sell_currency_id = fields.Many2one('res.currency', string='Sell Currency', required=True, tracking=True)
    sell_conversion_rate = fields.Float(string='Sell Exchange', default=1, tracking=True, digits=(16, 3))
    sell_amount_rate = fields.Monetary(string='Sell Rate per Unit', currency_field='sell_currency_id', tracking=True)
    debtor_partner_id = fields.Many2one('res.partner', string='Debtor', tracking=True)
    debtor_address_id = fields.Many2one('res.partner', string='Debtor Address', domain="['|', ('parent_id', '=', debtor_partner_id), ('id', '=', debtor_partner_id)]", tracking=True)
    sell_remarks = fields.Text(tracking=True)
    sell_currency_mismatch = fields.Boolean(compute='_compute_currency_mismatch', tracking=True)

    total_cost_amount = fields.Monetary(string='Cost Amount (Exl. Tax)', compute='_compute_total_cost_amount', store=True, tracking=True)
    total_sell_amount = fields.Monetary(string='Sell Amount (Exl. Tax)', compute='_compute_total_sell_amount', store=True, tracking=True)

    # Chart of Accounts
    property_account_income_id = fields.Many2one(
        'account.account', string="Receivable Account",
        domain="['&', '&', '&', ('deprecated', '=', False), ('internal_type','=','other'), ('company_id', '=', company_id), ('is_off_balance', '=', False), ('internal_group', '=', 'income')]",
        context="{'default_internal_group': 'income'}",
        company_dependent=True
    )
    property_account_expense_id = fields.Many2one(
        'account.account', string="Payable Account",
        domain="['&', '&', '&', ('deprecated', '=', False), ('internal_type','=','other'), ('company_id', '=', company_id), ('is_off_balance', '=', False), ('internal_group', '=', 'expense')]",
        context="{'default_internal_group': 'expense'}",
        company_dependent=True
    )

    estimated_margin = fields.Monetary(string='Estimated Margin', compute='_compute_estimated_margin', store=True, tracking=True)
    estimated_margin_percentage = fields.Float(string='Estimated Margin(%)', compute='_compute_estimated_margin_percentage', store=True, tracking=True)

    @api.depends('measurement_basis_id')
    def _compute_is_container_type_basis(self):
        for rec in self:
            rec.is_container_type_basis = rec.measurement_basis_id and rec.measurement_basis_id == self.env.ref('freight_base.measurement_basis_container_type')

    @api.constrains('measurement_basis_id', 'quantity')
    @api.onchange('measurement_basis_id', 'quantity')
    def _check_values_for_measurement_basis(self):
        measurement_basis_shipment = self.env.ref('freight_base.measurement_basis_shipment')
        measurement_container_count = self.env.ref('freight_base.measurement_basis_container_count')
        measurement_basis_teus = self.env.ref('freight_base.measurement_basis_teu')
        measurement_basis_weight = self.env.ref('freight_base.measurement_basis_weight')
        measurement_basis_volume = self.env.ref('freight_base.measurement_basis_volume')
        measurement_basis_chargeable = self.env.ref('freight_base.measurement_basis_chargeable')

        integer_measurement_basis = [measurement_basis_shipment, measurement_container_count, measurement_basis_teus]
        decimal_measurement_basis = [measurement_basis_weight, measurement_basis_volume, measurement_basis_chargeable]

        for rec in self:
            if rec.measurement_basis_id in integer_measurement_basis and (not rec.quantity.is_integer() or rec.quantity < 1):
                raise ValidationError(_('For Measurement Basis:%s - Only integer values greater than or equal to 1 allowed.') % (rec.measurement_basis_id.name))
            if rec.measurement_basis_id in decimal_measurement_basis and rec.quantity <= 0:
                raise ValidationError(_('For Measurement Basis:%s - Only Greater than 0 values should be allowed .') % (rec.measurement_basis_id.name))

    def _inverse_creditor_partner(self):
        vendor_party = self.env.ref('freight_base.org_type_vendor', raise_if_not_found=False)
        if vendor_party:
            self.mapped('creditor_partner_id').write({'category_ids': [(4, vendor_party.id)]})

    @api.depends('total_cost_amount', 'total_sell_amount')
    def _compute_estimated_margin(self):
        for charge in self:
            charge.estimated_margin = charge.total_sell_amount - charge.total_cost_amount

    @api.depends('estimated_margin', 'total_sell_amount')
    def _compute_estimated_margin_percentage(self):
        for charge in self:
            if charge.total_sell_amount <= 0:
                charge.estimated_margin_percentage = 0.0
            else:
                charge.estimated_margin_percentage = (charge.estimated_margin * 100) / charge.total_sell_amount

    @api.depends('cost_currency_id', 'sell_currency_id')
    def _compute_currency_mismatch(self):
        for rec in self:
            rec.cost_currency_mismatch = rec.cost_currency_id and rec.currency_id != rec.cost_currency_id
            rec.sell_currency_mismatch = rec.sell_currency_id and rec.currency_id != rec.sell_currency_id

    def _get_conversion_rate(self, currency):
        self.ensure_one()
        currency = self.env['res.currency'].sudo().with_context(company_id=self.company_id.id).search([('id', '=', currency.id)], limit=1)
        return 1/((currency and currency.rate) or 1)

    @api.onchange('sell_currency_id')
    def _onchange_sell_currency_id(self):
        for rec in self:
            rec.sell_conversion_rate = self._get_conversion_rate(rec.sell_currency_id)

    @api.onchange('cost_currency_id')
    def _onchange_cost_currency_id(self):
        for rec in self:
            rec.cost_conversion_rate = self._get_conversion_rate(rec.cost_currency_id)

    @api.depends('cost_currency_id', 'cost_amount_rate', 'quantity', 'cost_conversion_rate', 'cost_currency_mismatch')
    def _compute_total_cost_amount(self):
        for charge in self:
            conversion_rate = 1 if not charge.cost_currency_mismatch else charge.cost_conversion_rate
            charge.total_cost_amount = round(charge.cost_amount_rate * charge.quantity * conversion_rate, 3)

    @api.depends('sell_currency_id', 'sell_amount_rate', 'quantity', 'sell_conversion_rate', 'sell_currency_mismatch')
    def _compute_total_sell_amount(self):
        for charge in self:
            conversion_rate = 1 if not charge.sell_currency_mismatch else charge.sell_conversion_rate
            charge.total_sell_amount = round(charge.sell_amount_rate * charge.quantity * conversion_rate, 3)

    def action_update_cost_rate(self):
        self._onchange_cost_currency_id()

    def action_update_sell_rate(self):
        self._onchange_sell_currency_id()

    @api.onchange('creditor_partner_id')
    def _onchange_creditor_partner_id(self):
        self.update({'creditor_address_id': False})

    @api.onchange('debtor_partner_id')
    def _onchange_debtor_partner_id(self):
        self.update({'debtor_address_id': False})
