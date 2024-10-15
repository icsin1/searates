from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MasterShipmentChargeCost(models.Model):
    _name = 'master.shipment.charge.cost'
    _inherit = 'mixin.freight.charge'
    _description = 'Master Shipment Cost Charge'
    _check_company_auto = True

    @api.depends('bill_currency_id', 'amount_currency_id', 'move_line_ids')
    def _compute_bill_conversion_rate(self):
        currency_exchange_rate = False
        for rec in self:
            if rec.bill_currency_id != rec.amount_currency_id:
                if self._context.get('currency_exchange_rate'):
                    currency_exchange_rate = self._context.get('currency_exchange_rate')
                else:
                    move_line_ids = rec.move_line_ids
                    move_id = move_line_ids[0].move_id if move_line_ids else False
                    if move_id and rec.amount_currency_id.id == rec.currency_id.id:
                        currency_exchange_rate = move_id.currency_exchange_rate or 1
                    else:
                        currency_exchange_rate = move_line_ids and move_line_ids[0].currency_exchange_rate or 1
            else:
                currency_exchange_rate = rec.amount_conversion_rate
            if currency_exchange_rate:
                rec.bill_conversion_rate = rec.amount_currency_id.with_context(currency_exchange_rate=currency_exchange_rate)\
                    ._get_conversion_rate(rec.amount_currency_id, rec.bill_currency_id,
                                          rec.master_shipment_id.company_id,
                                          rec.master_shipment_id.shipment_date) if rec.bill_currency_id else 1
            else:
                rec.bill_conversion_rate = rec.bill_conversion_rate or 1

    @api.depends('total_currency_amount', 'bill_conversion_rate')
    def _compute_bill_currency_amount(self):
        for rec in self:
            rec.bill_currency_amount = rec.total_currency_amount * rec.bill_conversion_rate

    @api.depends('house_charge_cost_ids.status', 'move_line_ids')
    def _compute_has_bill(self):
        for shipment in self:
            shipment.has_bill = bool(shipment.house_charge_cost_ids.filtered(lambda charge: charge.status in ('partial', 'fully_billed'))) or shipment.move_line_ids

    @api.depends('move_line_ids', 'move_line_ids.parent_state')
    def _compute_bill_currency_id(self):
        for rec in self:
            rec.bill_currency_id = rec.move_line_ids and rec.move_line_ids[0].move_id.currency_id.id or False

    @api.depends('bill_currency_amount', 'move_line_ids', 'move_line_ids.amount_currency',
                 'move_line_ids.parent_state', 'house_charge_cost_ids.move_line_ids',
                 'house_charge_cost_ids.move_line_ids.amount_currency',
                 'house_charge_cost_ids.move_line_ids.parent_state')
    def _compute_actual_billed_amount(self):
        for rec in self:
            master_move_lines = rec.move_line_ids.filtered(lambda m: m.parent_state != 'cancel')
            house_move_lines = rec.house_charge_cost_ids.move_line_ids.filtered(lambda m: m.parent_state != 'cancel')
            actual_billed_amount = False
            if master_move_lines:
                actual_billed_amount = abs(sum(master_move_lines.mapped('amount_currency')))  # Amount need to be in absolute
            elif house_move_lines:
                actual_billed_amount = abs(
                    sum(house_move_lines.mapped('amount_currency')))  # Amount need to be in absolute
            rec.actual_billed_amount = actual_billed_amount

    @api.depends('bill_currency_amount', 'actual_billed_amount', 'bill_conversion_rate')
    def _compute_residual_amount(self):
        for rec in self:
            rec.amount_residual = rec.bill_currency_amount - rec.actual_billed_amount
            reverse_conversion_rate = 1 / rec.bill_conversion_rate
            rec.amount_currency_residual = reverse_conversion_rate * rec.amount_residual
            rec.total_residual_amount = rec.amount_currency_residual * rec.amount_conversion_rate

    @api.depends('quantity', 'amount_rate')
    def _compute_total_currency_amount(self):
        for rec in self:
            rec.total_bill_amount = (round(rec.amount_rate, rec.amount_currency_id.decimal_places) * rec.quantity)
            rec.total_currency_amount = rec.total_bill_amount - rec.total_credit_note_amount

    @api.depends('currency_id', 'move_line_ids', 'move_line_ids', 'move_line_ids.move_id.state',
                 'move_line_ids.move_id.amount_total', 'move_line_ids.move_id.amount_residual',
                 'move_line_ids.move_id.currency_id')
    def _compute_total_credit_amount(self):
        for cost_charge in self:
            credit_move_lines = cost_charge.move_line_ids.filtered(
                lambda line: line.house_shipment_charge_cost_id == cost_charge and line.move_id.state != 'cancel' and line.move_id.move_type == 'in_refund'
            )
            invoice_amount = 0
            total_qty = 0
            for move_line in credit_move_lines:
                invoice_amount += move_line.price_subtotal
                total_qty += move_line.quantity
            cost_charge.count_credit_note = len(credit_move_lines)
            cost_charge.total_credit_note_amount = invoice_amount
            cost_charge.total_credit_note_qty = total_qty

    master_shipment_id = fields.Many2one('freight.master.shipment', required=True, ondelete='cascade')
    parent_packaging_mode = fields.Selection(related='master_shipment_id.packaging_mode')
    transport_mode_id = fields.Many2one('transport.mode', related='master_shipment_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    domain_measurement_ids = fields.Many2many('freight.measurement.basis', string='Domain Measurement Basis', compute='_compute_domain_measurement_basis', store=True)
    company_id = fields.Many2one('res.company', related='master_shipment_id.company_id', string='Company', tracking=True, store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Local Currency', tracking=True, store=True)

    tax_ids = fields.Many2many('account.tax', 'master_shipment_cost_charges_taxes_rel', 'master_charge_id', 'tax_id', string='Taxes', copy=False, tracking=True,
                               domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]")
    property_account_id = fields.Many2one(
        'account.account', string="Cost Account",
        domain="['&', '&', '&', ('deprecated', '=', False), ('internal_type', '=', 'other'), ('company_id', '=', company_id), ('is_off_balance', '=', False), ('internal_group', '=', 'expense')]",
        context="{'default_internal_group': 'expense'}"
    )

    # Creditors/vendors
    partner_id = fields.Many2one('res.partner', required=True, string='Creditor', tracking=True, domain="[('category_ids.is_vendor', '=', True)]", inverse='_inverse_partner')
    partner_address_id = fields.Many2one('res.partner', string='Creditor Address',
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('parent_id', '=', partner_id), ('id', '=', partner_id)]",
                                         tracking=True)

    status = fields.Selection([
        ('no', 'To Adjust'),
        ('adjusted', 'Adjusted to House'),
        ('partial', 'Partial Billed'),
        ('fully_billed', 'Fully Billed'),
    ], default='no', tracking=True, compute='_compute_status', store=True)

    # Adjusted to houses
    house_charge_cost_ids = fields.One2many('house.shipment.charge.cost', 'master_shipment_cost_charge_id', 'House Costs')
    # Linked Revenue
    revenue_line_id = fields.Many2one('master.shipment.charge.revenue', string='Revenue Mapping', domain="[('master_shipment_id', '=', master_shipment_id), ('product_id', '=', product_id)]",
                                      inverse='_inverse_cost_on_revenue')
    has_bill = fields.Boolean(compute="_compute_has_bill", store=True)
    bill_currency_id = fields.Many2one('res.currency', string='Invoice Currency', compute='_compute_bill_currency_id',
                                       store=True)
    bill_conversion_rate = fields.Float(default=1, compute='_compute_bill_conversion_rate', store=True, digits='Currency Exchange Rate')
    bill_currency_amount = fields.Monetary(currency_field='bill_currency_id', compute='_compute_bill_currency_amount',
                                           store=True)
    actual_billed_amount = fields.Monetary('Invoiced Amount', currency_field='bill_currency_id',
                                           compute='_compute_actual_billed_amount', store=True)
    amount_residual = fields.Monetary('Due Amount To Invoice', currency_field='bill_currency_id',
                                      compute='_compute_residual_amount', store=True)
    amount_currency_residual = fields.Monetary('Due Amount', currency_field='amount_currency_id',
                                               compute='_compute_residual_amount', store=True)
    total_residual_amount = fields.Monetary('Total Due Amount', compute='_compute_residual_amount', store=True)

    total_bill_amount = fields.Monetary('Total Bill', currency_field='amount_currency_id',
                                        compute='_compute_total_currency_amount', store=True)
    total_credit_note_amount = fields.Monetary('Total Debit Note Amt.', currency_field='amount_currency_id',
                                               compute='_compute_total_credit_amount', store=True)
    total_credit_note_qty = fields.Integer('Total Debit Note QTY.', compute='_compute_total_credit_amount', store=True)
    count_credit_note = fields.Integer(compute='_compute_total_credit_amount', store=True)
    move_line_ids = fields.One2many('account.move.line', 'master_shipment_charge_cost_id', string='Journal Items')

    def _modification_line_restrict_states(self):
        return ['adjusted']

    def _inverse_cost_on_revenue(self):
        for cost in self:
            if not self.env.context.get('_ignore_inverse'):
                # Adding cost line on revenue
                cost.revenue_line_id.with_context(_ignore_inverse=True).cost_line_id = cost.id
                # Un-setting other already present value from cost other than current record
                (cost.master_shipment_id.cost_charge_ids).filtered(
                    lambda c: c.revenue_line_id == cost.revenue_line_id and c != cost
                ).with_context(_ignore_inverse=True).write({'revenue_line_id': False})
            # Un-setting other already present value
            (cost.master_shipment_id.revenue_charge_ids - cost.revenue_line_id).filtered(lambda c: c.cost_line_id == cost).write({'cost_line_id': False})

    def _inverse_partner(self):
        vendor_party = self.env.ref('freight_base.org_type_vendor', raise_if_not_found=False)
        if vendor_party:
            self.mapped('partner_id').write({'category_ids': [(4, vendor_party.id)]})

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

    @api.depends('house_charge_cost_ids', 'house_charge_cost_ids.status')
    def _compute_status(self):
        for rec in self:
            status = 'no'
            if rec.house_charge_cost_ids:
                status = 'adjusted'
            move_line_ids = rec.move_line_ids or rec.house_charge_cost_ids.move_line_ids
            if rec.amount_currency_residual <= 0 and move_line_ids:
                status = 'fully_billed'
            elif rec.total_currency_amount != rec.amount_currency_residual and move_line_ids:
                status = 'partial'
            rec.status = status

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product = self.product_id
        if product:
            self.charge_description = product.name
            self.measurement_basis_id = product.measurement_basis_id

            self.amount_currency_id = self.company_id.currency_id if not self.amount_currency_id else self.amount_currency_id
            self.amount_rate = product.standard_price
            self.tax_ids = product.supplier_taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
            self.property_account_id = product.with_company(self.company_id)._get_product_accounts()['expense']

    def unlink(self):
        for rec in self:
            if rec.status in rec._modification_line_restrict_states():
                raise UserError(_("Charges that have been adjusted to house cannot be deleted!"))
            if rec.status == 'fully_billed':
                raise UserError(_('Charges are fully billed cannot be deleted!'))
        return super().unlink()

    def action_adjust_costs_with_houses(self):
        shipment = self.mapped('master_shipment_id')
        measurement_basis = self.mapped('measurement_basis_id')
        container_type_ids = self.mapped('container_type_id')
        pending_adjust_to_house = self.filtered(lambda charge: charge.status == "no")
        if shipment.state == 'cancelled':
            raise UserError(_("Can not adjust charges of cancelled shipment."))

        if len(measurement_basis) != 1:
            raise UserError(_("That different UOM can not be adjusted at the same time."))
        if container_type_ids and len(container_type_ids) != 1:
            raise UserError(_("That different Container Type can not be adjusted at the same time."))
        if not pending_adjust_to_house:
            raise UserError(_("The selected costs lines are already adjusted to house shipments."))
        # Adjustment request for charge with house shipments
        return {
            'name': 'Adjust Cost Lines to House Shipments',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.adjust.charge.with.house',
            'context': {
                'default_adjust_mode': 'cost',
                'default_master_shipment_id': shipment.id,
                'default_measurement_basis_id': measurement_basis[0].id,
                'default_house_shipment_ids': [(6, False, shipment.house_shipment_ids.ids)],
                'default_measure_container_type_id': container_type_ids and container_type_ids[0].id or False,
                'default_cost_charge_ids': [(6, False, pending_adjust_to_house.ids)],
                'default_line_ids': [(0, 0, {
                    'shipment_id': house_shipment.id
                }) for house_shipment in shipment.house_shipment_ids]
            }
        }

    def action_unadjust_cost_charges(self):

        adjusted_lines = self.filtered(lambda line: line.status in ('adjusted', 'fully_billed', 'partial'))
        if adjusted_lines and adjusted_lines.house_charge_cost_ids:
            houses = adjusted_lines.house_charge_cost_ids.mapped('house_shipment_id.name')
            adjusted_lines.house_charge_cost_ids.unlink()
            self.notify_user(_('Charges Un-Adjusted'), _('Charges Un-Adjusted from {}'.format(','.join(houses))), 'success')
        else:
            raise UserError(_('Nothing to Un-adjust'))

    def action_create_vendor_bill(self):
        adjusted_charges = self.filtered(lambda line: line.status != "no")
        if not adjusted_charges:
            raise UserError(_("You need to first adjust charge(s) with house to generate bill from master."))
        charges_to_bill = adjusted_charges.filtered(lambda line: line.status != "fully_billed")
        if not charges_to_bill:
            raise UserError(_("Nothing to bill."))
        if charges_to_bill[0].master_shipment_id.state == 'cancelled':
            raise UserError(_("Can not generate bill of cancelled shipment."))

        invoiced_from_house = self.filtered(lambda line: line.status in ['fully_billed', 'partial'] and not line.move_line_ids)
        if invoiced_from_house:
            raise UserError(_("You can not create bills from Master as you already initiated billing from house level."))
        action = self.env.ref('freight_management_charges.mastershipment_charge_bill_wizard_action').sudo().read([])[0]
        cash_rounding_id = False
        if self.env.user.has_group('account.group_cash_rounding'):
            cash_rounding_id = self.env['account.cash.rounding'].search([], limit=1).id
        action['context'] = {
            'default_charge_ids': [(6, False, charges_to_bill.ids)],
            'default_currency_id': self.company_id.currency_id.id,
            'default_master_shipment_id': charges_to_bill[0].master_shipment_id.id,
            'default_invoice_cash_rounding_id': cash_rounding_id
        }
        return action

    def _get_action_for_view_moves(self):
        move_type = self.env.context.get('move_type')
        if not move_type:
            return
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_refund_type" if move_type == 'in_refund' else 'account.action_move_in_invoice_type')
        action['context'] = {'default_house_shipment_id': self.id, 'default_move_type': move_type, 'create': 0, 'search_default_posted': 1}
        return action, move_type

    def action_open_moves(self):
        self.ensure_one()

        action, move_type = self._get_action_for_view_moves()
        if not move_type:
            return

        moves = self.move_line_ids.mapped('move_id').filtered(lambda x: x.move_type == move_type)
        if len(moves) > 1:
            action['domain'] = [('id', 'in', moves.ids)]
            return action

        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        action['views'] = form_view + [(state, view) for state, view in action.get('views', []) if view != 'form']
        action['res_id'] = moves.id
        return action

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                addresses = self.partner_id.get_default_addresses()
                rec.partner_address_id = addresses and addresses[0]
