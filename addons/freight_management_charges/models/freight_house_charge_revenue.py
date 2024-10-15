from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HouseShipmentChargeRevenue(models.Model):
    _name = 'house.shipment.charge.revenue'
    _inherit = 'mixin.freight.charge'
    _description = 'House Shipment Revenue Charge'
    _check_company_auto = True

    house_shipment_id = fields.Many2one('freight.house.shipment', required=True, ondelete='cascade')
    parent_packaging_mode = fields.Selection(related='house_shipment_id.packaging_mode')
    master_shipment_id = fields.Many2one('freight.master.shipment', related='house_shipment_id.parent_id', store=True, string='Master Shipment ')
    transport_mode_id = fields.Many2one('transport.mode', related='house_shipment_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    domain_measurement_ids = fields.Many2many('freight.measurement.basis', string='Domain Measurement Basis', compute='_compute_domain_measurement_basis', store=True)

    company_id = fields.Many2one('res.company', related='house_shipment_id.company_id', string='Company', tracking=True, store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Local Currency', tracking=True, store=True)

    tax_ids = fields.Many2many('account.tax', 'house_shipment_charges_taxes_rel', 'house_charge_id', 'tax_id',
                               string='Taxes', copy=False, tracking=True, domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'sale')]")
    property_account_id = fields.Many2one(
        'account.account', string="Revenue Account",
        domain="['&', '&', '&', ('deprecated', '=', False), ('internal_type','=','other'), ('company_id', '=', company_id), ('is_off_balance', '=', False), ('internal_group', '=', 'income')]",
        context="{'default_internal_group': 'income'}"
    )

    # Amount
    allowed_partner_ids = fields.Many2many('res.partner', compute='_compute_allowed_partner_ids')
    partner_id = fields.Many2one('res.partner', string='Debtor', tracking=True,
                                 domain="[('id', 'in', allowed_partner_ids)]")
    partner_address_id = fields.Many2one('res.partner', string='Debtor Address', tracking=True,
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('parent_id', '=', partner_id), ('id', '=', partner_id)]")
    move_line_ids = fields.One2many('account.move.line', 'house_shipment_charge_revenue_id', string='Journal Items')

    # Note that, if invoice currency is set, new invoice (in case of partial) must need to be created with this currency
    # Below fields are required to manage invoice reconciliation
    # Incase of, charge is generated in USD and user creating invoice in AED, we will store
    # Currency as AED, conversion rate for USD to AED and
    # actual invoice amount and due amount will be validated based on AED amount
    # Note that, currency change validation has been applied on account.move if lines are linked with
    # this charges
    invoice_currency_id = fields.Many2one('res.currency', string='Invoice Currency', compute='_compute_invoice_currency_id', store=True)
    invoice_conversion_rate = fields.Float(default=1, compute='_compute_invoice_conversion_rate', store=True, digits='Currency Exchange Rate')
    invoice_currency_amount = fields.Monetary(currency_field='invoice_currency_id', compute='_compute_invoice_currency_amount', store=True)
    company_currency_amount = fields.Monetary(string='Company Currency Amount', store=True, compute='_compute_invoice_currency_amount', currency_field='currency_id')
    actual_invoiced_amount = fields.Monetary('Invoiced Amount', currency_field='invoice_currency_id', compute='_compute_actual_invoiced_amount', store=True)
    amount_residual = fields.Monetary('Due Amount To Invoice', currency_field='invoice_currency_id', compute='_compute_residual_amount', store=True)
    amount_currency_residual = fields.Monetary('Due Amount', currency_field='amount_currency_id', compute='_compute_residual_amount', store=True, group_operator=False)
    total_residual_amount = fields.Monetary('Total Due Amount', compute='_compute_residual_amount', store=True)
    invoiced_amount = fields.Monetary('Invoiced Amount (Incl. Tax)', currency_field='currency_id', compute='_compute_invoice_received_amount', store=True)
    invoice_received_amount = fields.Monetary('Invoice Received Amount (Incl. Tax)', currency_field='currency_id', compute='_compute_invoice_received_amount', store=True)

    total_bill_amount = fields.Monetary('Total Bill', currency_field='amount_currency_id', compute='_compute_total_currency_amount', store=True)
    total_credit_note_amount = fields.Monetary('Total Credit Note Amt.', currency_field='amount_currency_id', compute='_compute_total_credit_amount', store=True)
    total_credit_note_qty = fields.Integer('Total Credit Note QTY.', compute='_compute_total_credit_amount', store=True)
    count_credit_note = fields.Integer(compute='_compute_total_credit_amount', store=True)

    status = fields.Selection([
        ('no', 'To Invoice'),
        ('partial', 'Partial Invoice'),
        ('fully_invoiced', 'Fully Invoice'),
    ], compute='_compute_invoice_status', store=True, tracking=True)
    parent_id = fields.Many2one('freight.master.shipment', related="house_shipment_id.parent_id", readonly=False)
    allowed_house_shipment_ids = fields.Many2many('freight.house.shipment',
                                                  related="parent_id.attached_house_shipment_ids")

    # Adjustment field from master
    master_shipment_revenue_charge_id = fields.Many2one('master.shipment.charge.revenue', ondelete='set null')
    # Linked cost
    cost_line_id = fields.Many2one(
        'house.shipment.charge.cost', string='Cost Mapping', inverse="_inverse_revenue_on_cost", domain="[('house_shipment_id', '=', house_shipment_id), ('product_id', '=', product_id)]")

    part_bl_id = fields.Many2one('freight.house.shipment.part.bl', string="Part Bl")

    def _modification_line_restrict_states(self):
        return ['partial', 'fully_invoiced']

    def _inverse_revenue_on_cost(self):
        for revenue in self:
            if not self.env.context.get('_ignore_inverse'):
                # Adding revenue line on cost
                revenue.cost_line_id.with_context(_ignore_inverse=True).revenue_line_id = revenue.id
                # Un-setting other already present value from revenue other than current record
                (revenue.house_shipment_id.revenue_charge_ids).filtered(
                    lambda r: r.cost_line_id == revenue.cost_line_id and r != revenue
                ).with_context(_ignore_inverse=True).write({'cost_line_id': False})
            # Un-setting other already present value from cost
            (revenue.house_shipment_id.cost_charge_ids - revenue.cost_line_id).filtered(lambda c: c.revenue_line_id == revenue).write({'revenue_line_id': False})

    @api.depends('master_shipment_id', 'master_shipment_id.cargo_type_id', 'house_shipment_id')
    def _compute_domain_measurement_basis(self):
        for rec in self:
            cargo_type_id = rec.master_shipment_id.cargo_type_id or rec.house_shipment_id.cargo_type_id
            if cargo_type_id.is_package_group:
                domain = [('package_group', 'in', ['all', 'package'])]
            else:
                domain = [('package_group', 'in', ['all', 'container'])]
            rec.domain_measurement_ids = self.env['freight.measurement.basis'].search(domain).ids

    @api.depends('currency_id', 'move_line_ids', 'move_line_ids', 'move_line_ids.move_id.state', 'move_line_ids.move_id.amount_total', 'move_line_ids.move_id.amount_residual',
                 'move_line_ids.move_id.currency_id')
    def _compute_total_credit_amount(self):
        for revenue_charge in self:
            credit_move_lines = revenue_charge.move_line_ids.filtered(
                lambda line: line.house_shipment_charge_revenue_id == revenue_charge and line.move_id.state != 'cancel' and line.move_id.move_type == 'out_refund'
            )
            invoice_amount = 0
            total_qty = 0
            for move_line in credit_move_lines:
                if move_line.shipment_charge_currency_id != move_line.currency_id:
                    invoice_amount += move_line.price_subtotal / move_line.currency_exchange_rate
                else:
                    invoice_amount += move_line.price_subtotal
                total_qty += move_line.quantity
            revenue_charge.count_credit_note = len(credit_move_lines)
            revenue_charge.total_credit_note_amount = invoice_amount
            revenue_charge.total_credit_note_qty = total_qty

    @api.depends('quantity', 'amount_rate', 'total_credit_note_amount')
    def _compute_total_currency_amount(self):
        for rec in self:
            rec.total_bill_amount = (round(rec.amount_rate, rec.amount_currency_id.decimal_places) * rec.quantity)
            rec.total_currency_amount = rec.total_bill_amount - rec.total_credit_note_amount

    @api.depends('invoice_currency_id', 'amount_currency_id', 'move_line_ids')
    def _compute_invoice_conversion_rate(self):
        currency_exchange_rate = False
        for rec in self:
            if rec.invoice_currency_id != rec.amount_currency_id:
                if self._context.get('currency_exchange_rate'):
                    currency_exchange_rate = self._context.get('currency_exchange_rate')
                else:
                    move_lines = rec.move_line_ids and rec.move_line_ids.filtered(lambda move_line: move_line.move_id.state not in ('cancel'))
                    move_id = move_lines and move_lines[0].move_id or False
                    if move_id and rec.amount_currency_id.id == rec.currency_id.id:
                        currency_exchange_rate = move_id.currency_exchange_rate or 1
                    else:
                        currency_exchange_rate = move_lines and move_lines[0].currency_exchange_rate or 1
            else:
                currency_exchange_rate = rec.amount_conversion_rate

            rec.invoice_conversion_rate = currency_exchange_rate

    @api.depends('move_line_ids', 'move_line_ids.parent_state')
    def _compute_invoice_currency_id(self):
        for rec in self:
            rec.invoice_currency_id = rec.move_line_ids and rec.move_line_ids[0].move_id.currency_id.id or False

    @api.depends('total_currency_amount', 'invoice_conversion_rate')
    def _compute_invoice_currency_amount(self):
        for rec in self:
            invoice_conversion_rate = rec.invoice_conversion_rate if rec.move_line_ids else rec.amount_conversion_rate
            # Taking invoice conversion rate from amount_conversion_rate if no move lines present
            rec.invoice_currency_amount = rec.total_currency_amount * (invoice_conversion_rate if rec.amount_currency_id != rec.company_id.currency_id else 1)
            rec.company_currency_amount = rec.invoice_currency_amount

    @api.depends('house_shipment_id', 'house_shipment_id.shipment_partner_ids')
    def _compute_allowed_partner_ids(self):
        partner_obj = self.env['res.partner']
        for rec in self:
            partner_ids = rec.house_shipment_id.shipment_partner_ids.mapped('partner_id')
            if rec.house_shipment_id.is_part_bl:
                part_bl_ids = rec.house_shipment_id.part_bl_ids
                partner_ids |= part_bl_ids.mapped('client_id') + part_bl_ids.mapped('shipper_id') + part_bl_ids.mapped('consignee_id')
            partner_ids |= partner_obj.search(['|', ('company_id', '=', rec.company_id.id), ('company_id', '=', False), ('category_ids', '=', self.env.ref('freight_base.org_type_customer').id)])
            rec.allowed_partner_ids = [(6, False, partner_ids.ids)]

    @api.depends('invoice_currency_amount', 'actual_invoiced_amount', 'invoice_conversion_rate')
    def _compute_residual_amount(self):
        for rec in self:
            # Amount residual will be in base currency (rate is defined in amount_conversion_rate)
            rec.amount_residual = (rec.invoice_currency_amount - rec.actual_invoiced_amount)
            reverse_conversion_rate = 1/rec.amount_conversion_rate
            rec.amount_currency_residual = reverse_conversion_rate * rec.amount_residual
            rec.total_residual_amount = rec.amount_currency_residual * rec.amount_conversion_rate

    @api.depends('invoice_currency_amount', 'move_line_ids', 'move_line_ids.amount_currency', 'move_line_ids.parent_state')
    def _compute_actual_invoiced_amount(self):
        for rec in self:
            lines = rec.move_line_ids.filtered(lambda m: m.parent_state != 'cancel')
            # If invoice currency is not matching with company currency converting amount to company currency
            if lines.mapped('currency_id') not in rec.company_id.currency_id:
                rec.actual_invoiced_amount = abs(sum(lines.mapped('amount_currency'))) * rec.invoice_conversion_rate
            else:
                rec.actual_invoiced_amount = abs(sum(lines.mapped('amount_currency')))

    @api.depends('currency_id', 'move_line_ids', 'move_line_ids', 'move_line_ids.move_id.state', 'move_line_ids.move_id.amount_total', 'move_line_ids.move_id.amount_residual',
                 'move_line_ids.move_id.currency_id')
    def _compute_invoice_received_amount(self):
        for revenue_charge in self:
            moves = revenue_charge.move_line_ids.mapped('move_id').filtered(lambda m: m.state != 'cancel')
            invoice_amount, invoice_due_amount = 0.0, 0.0
            # Invoice Amount with currency conversion
            for move in moves:
                conversion_rate = move.currency_id.with_context(currency_exchange_rate=move.currency_exchange_rate)._get_conversion_rate(
                    move.currency_id, revenue_charge.currency_id, revenue_charge.company_id, revenue_charge.house_shipment_id.shipment_date)
                invoice_amount += move.amount_total * conversion_rate
                invoice_due_amount += move.amount_residual * conversion_rate

            revenue_charge.invoiced_amount = invoice_amount
            revenue_charge.invoice_received_amount = invoice_amount - invoice_due_amount

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get('default_house_shipment_id'):
            house_shipment = self.env['freight.house.shipment'].browse(self.env.context.get('default_house_shipment_id'))
            values['currency_id'] = house_shipment.company_id.currency_id.id
            values['amount_currency_id'] = house_shipment.company_id.currency_id.id
            values['partner_id'] = house_shipment.client_id.id
            values['partner_address_id'] = house_shipment.client_address_id.id
        return values

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product = self.product_id
        if product:
            self.charge_description = product.name
            self.measurement_basis_id = product.measurement_basis_id

            self.amount_currency_id = self.company_id.currency_id if not self.amount_currency_id else self.amount_currency_id
            self.amount_rate = product.list_price
            self.tax_ids = product.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
            self.property_account_id = product.with_company(self.company_id)._get_product_accounts()['income']

    @api.depends('amount_currency_residual', 'total_currency_amount')
    def _compute_invoice_status(self):
        for rec in self:
            status = 'no'
            move_line_ids = rec.move_line_ids.filtered(lambda line: line.move_id.state != 'cancel' and line.move_id.move_type in ['in_invoice', 'out_invoice'])
            if round(rec.amount_currency_residual) <= 0 and move_line_ids:
                status = 'fully_invoiced'
            elif round(rec.amount_currency_residual) > 0 and move_line_ids:
                status = 'partial'
            rec.status = status

    # Generating invoice
    def action_create_customer_invoice(self):
        charges_to_invoice = self.filtered(lambda inv: inv.status in ('no', 'partial'))
        if not charges_to_invoice:
            raise UserError(_("Nothing to invoice. For generated proforma invoice, You can generate invoice only from Proforma-Invoice."))

        self.check_charges_rate_per_unit('invoice')
        if charges_to_invoice[0].house_shipment_id.state == 'cancelled':
            raise UserError(_("Can not generate invoice of cancelled shipment."))

        action = self.env.ref('freight_management_charges.shipment_charge_invoice_wizard_action').sudo().read([])[0]
        cash_rounding_id = False
        if self.env.user.has_group('account.group_cash_rounding'):
            cash_rounding_id = self.env['account.cash.rounding'].search([], limit=1).id
        action['context'] = {
            'default_charge_ids': [(6, False, charges_to_invoice.ids)],
            'default_currency_id': self.company_id.currency_id.id,
            'default_house_shipment_id': charges_to_invoice[0].house_shipment_id.id,
            'default_invoice_cash_rounding_id': cash_rounding_id
        }
        return action

    def unlink(self):
        for rec in self:
            if rec.status in rec._modification_line_restrict_states():
                raise UserError(_("Charges that have been partially or fully invoiced cannot be deleted!"))
        if not self.env.context.get('_ignore_master_check'):
            # Removing all the adjusted lines from other house as well
            master_adjusted_lines = self.mapped('master_shipment_revenue_charge_id')
            if master_adjusted_lines:
                other_house_lines = master_adjusted_lines.house_charge_revenue_ids - self
                other_house_lines.with_context(_ignore_master_check=True).unlink()
        return super().unlink()

    def action_open_moves(self):
        self.ensure_one()

        move_type = self.env.context.get('move_type')
        if not move_type:
            return

        moves = self.move_line_ids.mapped('move_id').filtered(lambda x: x.move_type == move_type)
        if move_type == 'out_refund':
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_refund_type")
            action['context'] = {'default_house_shipment_id': self.id, 'default_move_type': 'out_refund', 'create': 0}
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
            action['context'] = {'default_house_shipment_id': self.id, 'default_move_type': 'out_invoice', 'create': 0}

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
