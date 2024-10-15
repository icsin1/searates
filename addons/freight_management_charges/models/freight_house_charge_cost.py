from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HouseShipmentChargeCost(models.Model):
    _name = 'house.shipment.charge.cost'
    _inherit = 'mixin.freight.charge'
    _description = 'House Shipment Cost Charge'
    _check_company_auto = True

    @api.depends('master_shipment_cost_charge_id.move_line_ids')
    def _compute_master_move_line_ids(self):
        for charge in self:
            charge.master_move_line_ids = charge.master_shipment_cost_charge_id.move_line_ids

    house_shipment_id = fields.Many2one('freight.house.shipment', required=True, ondelete='cascade')
    parent_packaging_mode = fields.Selection(related='house_shipment_id.packaging_mode')
    master_shipment_id = fields.Many2one('freight.master.shipment', related='house_shipment_id.parent_id', store=True)
    transport_mode_id = fields.Many2one('transport.mode', related='house_shipment_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    domain_measurement_ids = fields.Many2many('freight.measurement.basis', string='Domain Measurement Basis', compute='_compute_domain_measurement_basis', store=True)

    company_id = fields.Many2one('res.company', related='house_shipment_id.company_id', string='Company', tracking=True, store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Local Currency', tracking=True, store=True)

    tax_ids = fields.Many2many('account.tax', 'house_shipment_cost_charges_taxes_rel', 'house_charge_id', 'tax_id', string='Taxes', copy=False, tracking=True,
                               domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]")
    property_account_id = fields.Many2one(
        'account.account', string="Cost Account",
        domain="['&', '&', '&', ('deprecated', '=', False), ('internal_type', '=', 'other'), ('company_id', '=', company_id), ('is_off_balance', '=', False), ('internal_group', '=', 'expense')]",
        context="{'default_internal_group': 'expense'}"
    )

    # Amount
    partner_id = fields.Many2one('res.partner', string='Creditor', tracking=True,
                                 domain="[('category_ids.is_vendor', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 inverse='_inverse_partner', required=False)
    partner_address_id = fields.Many2one('res.partner', string='Creditor Address', tracking=True,
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('parent_id', '=', partner_id), ('id', '=', partner_id)]")
    move_line_ids = fields.One2many('account.move.line', 'house_shipment_charge_cost_id', string='Journal Items')

    # Note that, if bill currency is set, new bill (in case of partial) must need to be created with this currency
    # Below fields are required to manage bill reconciliation
    # Incase of, charge is generated in USD and user creating bill in AED, we will store
    # Currency as AED, conversion rate for USD to AED and
    # actual bill amount and due amount will be validated based on AED amount
    # Note that, currency change validation has been applied on account.move if lines are linked with
    # this charges
    bill_currency_id = fields.Many2one('res.currency', string='Invoice Currency', compute='_compute_bill_currency_id', store=True)
    bill_conversion_rate = fields.Float(default=1, compute='_compute_bill_conversion_rate', store=True, digits='Currency Exchange Rate')
    bill_currency_amount = fields.Monetary(currency_field='bill_currency_id', compute='_compute_bill_currency_amount', store=True)
    actual_billed_amount = fields.Monetary('Invoiced Amount', currency_field='bill_currency_id', compute='_compute_actual_billed_amount', store=True)
    amount_residual = fields.Monetary('Due Amount To Invoice', currency_field='bill_currency_id', compute='_compute_residual_amount', store=True)
    amount_currency_residual = fields.Monetary('Due Amount', currency_field='amount_currency_id', compute='_compute_residual_amount', store=True, group_operator=False)
    total_residual_amount = fields.Monetary('Total Due Amount', compute='_compute_residual_amount', store=True)

    total_bill_amount = fields.Monetary('Total Bill', currency_field='amount_currency_id', compute='_compute_total_currency_amount', store=True)
    total_credit_note_amount = fields.Monetary('Total Debit Note Amt.', currency_field='amount_currency_id', compute='_compute_total_credit_amount', store=True)
    total_credit_note_qty = fields.Integer('Total Debit Note QTY.', compute='_compute_total_credit_amount', store=True)
    count_credit_note = fields.Integer(compute='_compute_total_credit_amount', store=True)

    status = fields.Selection([
        ('no', 'To Bill'),
        ('partial', 'Partial Billed'),
        ('fully_billed', 'Fully Billed'),
    ], compute='_compute_bill_status', store=True, tracking=True)
    parent_id = fields.Many2one('freight.master.shipment', related="house_shipment_id.parent_id", readonly=False, string='Master Shipment ')
    allowed_house_shipment_ids = fields.Many2many('freight.house.shipment',
                                                  related="parent_id.attached_house_shipment_ids")
    # Adjustment field from master
    master_shipment_cost_charge_id = fields.Many2one('master.shipment.charge.cost', ondelete='set null')
    # Linked Revenue
    revenue_line_id = fields.Many2one(
        'house.shipment.charge.revenue', string='Revenue Mapping', inverse="_inverse_cost_on_revenue", domain="[('house_shipment_id', '=', house_shipment_id), ('product_id', '=', product_id)]")
    master_shipment_cost_charge_has_bill = fields.Boolean(related="master_shipment_cost_charge_id.has_bill", store=True)
    master_move_line_ids = fields.Many2many('account.move.line', 'master_cost_move_line_rel', string="Master Move Lines",
                                            compute="_compute_master_move_line_ids",
                                            store=True)

    def _modification_line_restrict_states(self):
        return ['partial', 'fully_billed']

    def _inverse_cost_on_revenue(self):
        for cost in self:
            if not self.env.context.get('_ignore_inverse'):
                # Adding cost line on revenue
                cost.revenue_line_id.with_context(_ignore_inverse=True).cost_line_id = cost.id
                # Un-setting other already present value from cost other than current record
                (cost.house_shipment_id.cost_charge_ids).filtered(
                    lambda c: c.revenue_line_id == cost.revenue_line_id and c != cost
                ).with_context(_ignore_inverse=True).write({'revenue_line_id': False})
            # Un-setting other already present value from revenue
            (cost.house_shipment_id.revenue_charge_ids - cost.revenue_line_id).filtered(lambda c: c.cost_line_id == cost).write({'cost_line_id': False})

    def _inverse_partner(self):
        vendor_party = self.env.ref('freight_base.org_type_vendor', raise_if_not_found=False)
        if vendor_party:
            self.mapped('partner_id').write({'category_ids': [(4, vendor_party.id)]})

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get('default_house_shipment_id'):
            house_shipment = self.env['freight.house.shipment'].browse(self.env.context.get('default_house_shipment_id'))
            values['house_shipment_id'] = house_shipment.id
            values['company_id'] = house_shipment.company_id.id
            values['currency_id'] = house_shipment.company_id.currency_id.id
            values['amount_currency_id'] = house_shipment.company_id.currency_id.id
        return values

    @api.depends('master_shipment_id', 'master_shipment_id.cargo_type_id', 'house_shipment_id')
    def _compute_domain_measurement_basis(self):
        for rec in self:
            cargo_type_id = rec.master_shipment_id.cargo_type_id or rec.house_shipment_id.cargo_type_id
            if cargo_type_id.is_package_group:
                domain = [('package_group', 'in', ['all', 'package'])]
            else:
                domain = [('package_group', 'in', ['all', 'container'])]
            rec.domain_measurement_ids = self.env['freight.measurement.basis'].search(domain).ids

    @api.depends('currency_id', 'move_line_ids', 'move_line_ids', 'move_line_ids.move_id.state',
                 'move_line_ids.move_id.amount_total', 'move_line_ids.move_id.amount_residual',
                 'move_line_ids.move_id.currency_id', 'master_move_line_ids', 'master_move_line_ids.move_id.state',
                 'master_move_line_ids.move_id.amount_total', 'master_move_line_ids.move_id.amount_residual',
                 'master_move_line_ids.move_id.currency_id')
    def _compute_total_credit_amount(self):
        for cost_charge in self:
            move_line_ids = cost_charge.move_line_ids + cost_charge.master_move_line_ids
            credit_move_lines = move_line_ids.filtered(
                lambda line: (
                    line.house_shipment_charge_cost_id == cost_charge or line.master_shipment_charge_cost_id == cost_charge.master_shipment_cost_charge_id
                ) and line.move_id.state != 'cancel' and line.move_id.move_type == 'in_refund'
            )
            invoice_amount = 0
            total_qty = 0
            for move_line in credit_move_lines:
                invoice_amount += move_line.price_subtotal
                total_qty += move_line.quantity
            cost_charge.count_credit_note = len(credit_move_lines)
            cost_charge.total_credit_note_amount = invoice_amount
            cost_charge.total_credit_note_qty = total_qty

    @api.depends('quantity', 'amount_rate', 'total_credit_note_amount', 'total_credit_note_qty')
    def _compute_total_currency_amount(self):
        for rec in self:
            rec.total_bill_amount = (round(rec.amount_rate, rec.amount_currency_id.decimal_places) * rec.quantity)
            credit_note_amount_per_shipment = rec.total_credit_note_qty
            if rec.total_credit_note_qty:
                credit_note_amount_per_shipment = (rec.total_credit_note_amount / rec.total_credit_note_qty) * rec.quantity
            rec.total_currency_amount = rec.total_bill_amount - credit_note_amount_per_shipment

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

    @api.depends('bill_currency_id', 'amount_currency_id', 'move_line_ids', 'master_move_line_ids')
    def _compute_bill_conversion_rate(self):
        currency_exchange_rate = False
        for rec in self:
            if rec.bill_currency_id != rec.amount_currency_id:
                if self._context.get('currency_exchange_rate'):
                    currency_exchange_rate = self._context.get('currency_exchange_rate')
                else:
                    move_line_ids = (rec.move_line_ids or rec.master_move_line_ids).filtered(lambda move_line: move_line.move_id.state not in ('cancel'))
                    move_id = move_line_ids[0].move_id if move_line_ids else False
                    if move_id and rec.amount_currency_id.id == rec.currency_id.id:
                        currency_exchange_rate = move_id.currency_exchange_rate or 1
                    else:
                        currency_exchange_rate = move_line_ids and move_line_ids[0].currency_exchange_rate or 1
            else:
                currency_exchange_rate = rec.amount_conversion_rate

            if currency_exchange_rate:
                rec.bill_conversion_rate = rec.amount_currency_id.with_context(currency_exchange_rate=currency_exchange_rate)._get_conversion_rate(
                    rec.amount_currency_id, rec.bill_currency_id, rec.house_shipment_id.company_id, rec.house_shipment_id.shipment_date
                ) if rec.bill_currency_id else 1
            else:
                rec.bill_conversion_rate = rec.bill_conversion_rate or 1

    @api.depends('move_line_ids', 'move_line_ids.parent_state', 'master_move_line_ids',
                 'master_move_line_ids.parent_state')
    def _compute_bill_currency_id(self):
        for rec in self:
            move_line_ids = rec.move_line_ids or rec.master_move_line_ids
            rec.bill_currency_id = move_line_ids and move_line_ids[0].move_id.currency_id.id or False

    @api.depends('total_currency_amount', 'bill_conversion_rate')
    def _compute_bill_currency_amount(self):
        for rec in self:
            rec.bill_currency_amount = rec.total_currency_amount * rec.bill_conversion_rate

    @api.depends('bill_currency_amount', 'actual_billed_amount', 'bill_conversion_rate')
    def _compute_residual_amount(self):
        for rec in self:
            rec.amount_residual = rec.bill_currency_amount - rec.actual_billed_amount
            reverse_conversion_rate = 1/rec.bill_conversion_rate
            rec.amount_currency_residual = reverse_conversion_rate * rec.amount_residual
            rec.total_residual_amount = rec.amount_currency_residual * rec.amount_conversion_rate

    @api.depends('bill_currency_amount', 'move_line_ids', 'move_line_ids.amount_currency', 'move_line_ids.parent_state',
                 'master_move_line_ids', 'master_move_line_ids.amount_currency',
                 'master_move_line_ids.parent_state')
    def _compute_actual_billed_amount(self):
        for rec in self:
            house_move_lines = rec.move_line_ids.filtered(lambda m: m.parent_state != 'cancel')
            master_move_lines = rec.master_move_line_ids.filtered(lambda m: m.parent_state != 'cancel')
            actual_billed_amount = abs(sum(house_move_lines.mapped('amount_currency')))
            if master_move_lines:
                adjustment_ratio = rec.quantity / (rec.master_shipment_cost_charge_id.quantity or 1)
                master_move_line_total = abs(sum(master_move_lines.mapped('amount_currency')))
                actual_billed_amount += (master_move_line_total * adjustment_ratio)
            rec.actual_billed_amount = actual_billed_amount  # Amount need to be in absolute

    @api.depends('amount_currency_residual', 'total_currency_amount', 'move_line_ids', 'master_move_line_ids')
    def _compute_bill_status(self):
        for rec in self:
            status = 'no'
            move_line_ids = (rec.move_line_ids.filtered(lambda line: line.move_id.state != 'cancel' and line.move_id.move_type in ['in_invoice', 'out_invoice', 'entry']) or
                             rec.master_move_line_ids.filtered(lambda line: line.move_id.state != 'cancel' and line.move_id.move_type in ['in_invoice', 'out_invoice', 'entry']))
            if rec.amount_currency_residual <= 0 and move_line_ids:
                status = 'fully_billed'
            elif rec.total_currency_amount != rec.amount_currency_residual and move_line_ids:
                status = 'partial'
            rec.status = status

    # Generating bill
    def action_create_vendor_bill(self):
        charges_to_bill = self.filtered(lambda line: line.status in ('no', 'partial'))
        if not charges_to_bill:
            raise UserError(_("Nothing to bill."))
        if charges_to_bill[0].house_shipment_id.state == 'cancelled':
            raise UserError(_("Can not generate bill of cancelled shipment."))

        charges_to_bill = self.filtered(lambda line: not line.master_move_line_ids)
        if not charges_to_bill:
            raise UserError(_("The bill has already been initiated from the master shipment."))

        self.check_charges_rate_per_unit('vendor bill')
        action = self.env.ref('freight_management_charges.shipment_charge_bill_wizard_action').sudo().read([])[0]
        cash_rounding_id = False
        if self.env.user.has_group('account.group_cash_rounding'):
            cash_rounding_id = self.env['account.cash.rounding'].search([], limit=1).id
        action['context'] = {
            'default_charge_ids': [(6, False, charges_to_bill.ids)],
            'default_currency_id': self.company_id.currency_id.id,
            'default_house_shipment_id': charges_to_bill[0].house_shipment_id.id,
            'default_invoice_cash_rounding_id': cash_rounding_id
        }
        return action

    def unlink(self):
        for rec in self:
            if rec.status in rec._modification_line_restrict_states():
                raise UserError(_("Charges that have been partially or fully billed cannot be deleted!"))
        if not self.env.context.get('_ignore_master_check'):
            # Removing all the adjusted lines from other house as well
            master_adjusted_lines = self.mapped('master_shipment_cost_charge_id')
            if master_adjusted_lines:
                other_house_lines = master_adjusted_lines.house_charge_cost_ids - self
                other_house_lines.with_context(_ignore_master_check=True).unlink()
        return super().unlink()

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
        move_line_ids = self.move_line_ids + self.master_move_line_ids
        moves = move_line_ids.mapped('move_id').filtered(lambda x: x.move_type == move_type)

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
