from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MasterShipmentChargeRevenue(models.Model):
    _name = 'master.shipment.charge.revenue'
    _inherit = 'mixin.freight.charge'
    _description = 'Master Shipment Revenue Charge'
    _check_company_auto = True

    master_shipment_id = fields.Many2one('freight.master.shipment', required=True, ondelete='cascade')
    parent_packaging_mode = fields.Selection(related='master_shipment_id.packaging_mode')
    transport_mode_id = fields.Many2one('transport.mode', related='master_shipment_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    domain_measurement_ids = fields.Many2many('freight.measurement.basis', string='Domain Measurement Basis', compute='_compute_domain_measurement_basis', store=True)
    company_id = fields.Many2one('res.company', related='master_shipment_id.company_id', string='Company', tracking=True, store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Local Currency', tracking=True, store=True)

    partner_id = fields.Many2one('res.partner', required=False)
    tax_ids = fields.Many2many('account.tax', 'master_shipment_revenue_charges_taxes_rel', 'master_charge_id', 'tax_id', string='Taxes', copy=False, tracking=True,
                               domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'sale')]")
    property_account_id = fields.Many2one(
        'account.account', string="Revenue Account",
        domain="['&', '&', '&', ('deprecated', '=', False), ('internal_type', '=', 'other'), ('company_id', '=', company_id), ('is_off_balance', '=', False), ('internal_group', '=', 'expense')]",
        context="{'default_internal_group': 'expense'}"
    )

    status = fields.Selection([
        ('no', 'To Adjust'),
        ('adjusted', 'Adjusted to House'),
    ], default='no', tracking=True, compute='_compute_status', store=True)

    # Adjusted to houses
    house_charge_revenue_ids = fields.One2many('house.shipment.charge.revenue', 'master_shipment_revenue_charge_id', 'House Revenue')
    # Linked cost
    cost_line_id = fields.Many2one('master.shipment.charge.cost', string='Cost Mapping', domain="[('master_shipment_id', '=', master_shipment_id), ('product_id', '=', product_id)]",
                                   inverse='_inverse_cost_on_revenue')

    def _modification_line_restrict_states(self):
        return ['adjusted']

    def _inverse_cost_on_revenue(self):
        for revenue in self:
            if not self.env.context.get('_ignore_inverse'):
                # Adding revenue line on cost
                revenue.cost_line_id.with_context(_ignore_inverse=True).revenue_line_id = revenue.id
                # Un-setting other already present value from revenue other than current record
                (revenue.master_shipment_id.revenue_charge_ids).filtered(lambda r: r.cost_line_id == revenue.cost_line_id and r != revenue).with_context(_ignore_inverse=True).write({
                    'cost_line_id': False})
            # Un-setting other already present value
            (revenue.master_shipment_id.cost_charge_ids - revenue.cost_line_id).filtered(lambda c: c.revenue_line_id == revenue).write({'revenue_line_id': False})

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get('default_master_shipment_id'):
            master_shipment = self.env['freight.master.shipment'].browse(self.env.context.get('default_master_shipment_id'))
            values['master_shipment_id'] = master_shipment.id
            values['company_id'] = master_shipment.company_id.id
            values['currency_id'] = master_shipment.company_id.currency_id.id
            values['amount_currency_id'] = master_shipment.company_id.currency_id.id
        return values

    @api.depends('master_shipment_id', 'master_shipment_id.cargo_type_id')
    def _compute_domain_measurement_basis(self):
        for rec in self:
            cargo_type_id = rec.master_shipment_id.cargo_type_id
            if cargo_type_id.is_package_group:
                domain = [('package_group', 'in', ['all', 'package'])]
            else:
                domain = [('package_group', 'in', ['all', 'container'])]
            rec.domain_measurement_ids = self.env['freight.measurement.basis'].search(domain).ids

    @api.depends('house_charge_revenue_ids')
    def _compute_status(self):
        for rec in self:
            rec.status = 'no' if not rec.house_charge_revenue_ids else 'adjusted'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product = self.product_id
        if product:
            self.charge_description = product.name
            self.measurement_basis_id = product.measurement_basis_id

            self.amount_currency_id = self.company_id.currency_id if not self.amount_currency_id else self.amount_currency_id
            self.amount_rate = product.standard_price
            self.tax_ids = product.supplier_taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)

            self.property_account_id = product.with_company(self.company_id)._get_product_accounts()['income']

    def unlink(self):
        for rec in self:
            if rec.status in rec._modification_line_restrict_states():
                raise UserError(_("Charges that have been adjusted to house cannot be deleted!"))
        return super().unlink()

    def action_adjust_revenue_with_houses(self):
        shipment = self.mapped('master_shipment_id')
        measurement_basis = self.mapped('measurement_basis_id')
        container_type_ids = self.mapped('container_type_id')
        pending_adjust_to_house = self.filtered(lambda charge: charge.status == "no")
        if shipment.state == 'cancelled':
            raise UserError(_("Can not adjust charges of cancelled shipment."))

        if len(measurement_basis) != 1:
            raise UserError(_("Two different Measurement Basis can not be adjusted at the same time."))
        if container_type_ids and len(container_type_ids) != 1:
            raise UserError(_("That different Container Type can not be adjusted at the same time."))
        if not pending_adjust_to_house:
            raise UserError(_("The selected revenue lines are already adjusted to house shipments."))
        # Adjustment request for charge with house shipments
        return {
            'name': 'Adjust Revenue Lines to House Shipments',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.adjust.charge.with.house',
            'context': {
                'default_adjust_mode': 'revenue',
                'default_master_shipment_id': shipment.id,
                'default_measurement_basis_id': measurement_basis[0].id,
                'default_measure_container_type_id': container_type_ids and container_type_ids[0].id or False,
                'default_house_shipment_ids': [(6, False, shipment.house_shipment_ids.ids)],
                'default_revenue_charge_ids': [(6, False, pending_adjust_to_house.ids)],
                'default_line_ids': [(0, 0, {
                    'shipment_id': house_shipment.id
                }) for house_shipment in shipment.house_shipment_ids]
            }
        }

    def action_unadjust_revenue_charges(self):
        adjusted_lines = self.filtered(lambda line: line.status == 'adjusted')
        if adjusted_lines and adjusted_lines.house_charge_revenue_ids:
            houses = adjusted_lines.house_charge_revenue_ids.mapped('house_shipment_id.name')
            adjusted_lines.house_charge_revenue_ids.unlink()
            self.notify_user(_('Charges Un-Adjusted'), _('Charges Un-Adjusted from {}'.format(','.join(houses))), 'success')
        else:
            raise UserError(_('Nothing to Un-adjust'))
