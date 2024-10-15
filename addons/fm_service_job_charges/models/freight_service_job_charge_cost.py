from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ServiceJobChargeCost(models.Model):
    _name = 'service.job.charge.cost'
    _inherit = 'mixin.freight.charge'
    _description = 'Service Job Cost Charge'
    _check_company_auto = True

    service_job_id = fields.Many2one('freight.service.job', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', domain=lambda self: "['|', ('company_id', '=', company_id), ('company_id', '=', False), ('categ_id', '=', %s)]" % self.env.ref('fm_service_job.job_charge_category').id)
    measurement_basis_id = fields.Many2one('freight.measurement.basis', string='Measurement Basis', domain="[('is_job_measurement', '=', True)]")
    company_id = fields.Many2one('res.company', related='service_job_id.company_id', string='Company', tracking=True, store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Local Currency', tracking=True, store=True)

    tax_ids = fields.Many2many('account.tax', 'service_job_cost_charges_taxes_rel', 'service_job_charge_id', 'tax_id', string='Taxes', copy=False, tracking=True,
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
    move_line_ids = fields.One2many('account.move.line', 'service_job_charge_cost_id', string='Journal Items')

    # Note that, if bill currency is set, new bill (in case of partial) must need to be created with this currency
    # Below fields are required to manage bill reconciliation
    # Incase of, charge is generated in USD and user creating bill in AED, we will store
    # Currency as AED, conversion rate for USD to AED and
    # actual bill amount and due amount will be validated based on AED amount
    # Note that, currency change validation has been applied on account.move if lines are linked with
    # this charges
    bill_currency_id = fields.Many2one('res.currency', string='Invoice Currency', compute='_compute_bill_currency_id', store=True)
    bill_conversion_rate = fields.Float(default=1, compute='_compute_bill_conversion_rate', store=True, digits='Currency Exchange Rate')
    bill_currency_amount = fields.Monetary(currency_field='currency_id', compute='_compute_bill_currency_amount', store=True)
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
    # Linked Revenue
    revenue_line_id = fields.Many2one(
        'service.job.charge.revenue', string='Revenue Mapping', inverse="_inverse_cost_on_revenue", domain="[('service_job_id', '=', service_job_id), ('product_id', '=', product_id)]")

    def _modification_line_restrict_states(self):
        return ['partial', 'fully_billed']

    def _inverse_cost_on_revenue(self):
        for cost in self:
            if not self.env.context.get('_ignore_inverse'):
                # Adding cost line on revenue
                cost.revenue_line_id.with_context(_ignore_inverse=True).cost_line_id = cost.id
                # Un-setting other already present value from cost other than current record
                (cost.service_job_id.cost_charge_ids).filtered(lambda c: c.revenue_line_id == cost.revenue_line_id and c != cost).with_context(_ignore_inverse=True).write({'revenue_line_id': False})
            # Un-setting other already present value from revenue
            (cost.service_job_id.revenue_charge_ids - cost.revenue_line_id).filtered(lambda c: c.cost_line_id == cost).write({'cost_line_id': False})

    def _inverse_partner(self):
        vendor_party = self.env.ref('freight_base.org_type_vendor', raise_if_not_found=False)
        if vendor_party:
            self.mapped('partner_id').write({'category_ids': [(4, vendor_party.id)]})

    @api.onchange('container_type_id')
    def _onchange_container_type_id(self):
        for charge in self:
            if charge.is_container_type_basis and charge.container_type_id:
                charge.quantity = 1

    @api.onchange('measurement_basis_id')
    def _onchange_measurement_basis_id(self):
        charges_measure_dict = {
            self.env.ref('freight_base.measurement_basis_chargeable', raise_if_not_found=False): 'chargeable_kg',
            self.env.ref('freight_base.measurement_basis_volume', raise_if_not_found=False): 'volume_unit',
            self.env.ref('freight_base.measurement_basis_weight', raise_if_not_found=False): 'net_weight_unit'
        }
        for charge in self.filtered(lambda c: c.measurement_basis_id):
            column = charges_measure_dict.get(charge.measurement_basis_id)
            charge.quantity = charge.service_job_id[column] if column else 1

            if not charge.is_container_type_basis:
                charge.container_type_id = False

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get('default_service_job_id'):
            service_job = self.env['freight.service.job'].browse(self.env.context.get('default_service_job_id'))
            values['service_job_id'] = service_job.id
            values['company_id'] = service_job.company_id.id
            values['currency_id'] = service_job.company_id.currency_id.id
            values['amount_currency_id'] = service_job.company_id.currency_id.id
        return values

    @api.depends('currency_id', 'move_line_ids', 'move_line_ids', 'move_line_ids.move_id.state',
                 'move_line_ids.move_id.amount_total', 'move_line_ids.move_id.amount_residual',
                 'move_line_ids.move_id.currency_id')
    def _compute_total_credit_amount(self):
        for cost_charge in self:
            move_line_ids = cost_charge.move_line_ids
            credit_move_lines = move_line_ids.filtered(
                lambda l: (l.service_job_charge_cost_id == cost_charge) and l.move_id.state != 'cancel' and l.move_id.move_type == 'in_refund'
            )
            invoice_amount = 0
            total_qty = 0
            for move_line in credit_move_lines:
                invoice_amount += move_line.price_subtotal
                total_qty += move_line.quantity
            cost_charge.count_credit_note = len(credit_move_lines)
            cost_charge.total_credit_note_amount = invoice_amount
            cost_charge.total_credit_note_qty = total_qty

    @api.depends('quantity', 'amount_rate', 'total_credit_note_amount')
    def _compute_total_currency_amount(self):
        for rec in self:
            rec.total_bill_amount = (round(rec.amount_rate, rec.amount_currency_id.decimal_places) * rec.quantity)
            rec.total_currency_amount = rec.total_bill_amount - rec.total_credit_note_amount

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product = self.product_id
        if product:
            self.charge_description = self.charge_description or product.name
            self.measurement_basis_id = product.measurement_basis_id

            self.amount_currency_id = self.company_id.currency_id if not self.amount_currency_id else self.amount_currency_id
            self.amount_rate = product.standard_price
            self.tax_ids = product.supplier_taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)

            self.property_account_id = product.with_company(self.company_id)._get_product_accounts()['expense']

    @api.depends('bill_currency_id', 'amount_currency_id', 'move_line_ids', 'amount_conversion_rate')
    def _compute_bill_conversion_rate(self):
        currency_exchange_rate = False
        for rec in self:
            bill_currency = rec.move_line_ids[0].currency_id if rec.move_line_ids else rec.bill_currency_id
            if bill_currency and bill_currency != rec.amount_currency_id:
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
                rec.bill_conversion_rate = rec.amount_currency_id.with_context(currency_exchange_rate=currency_exchange_rate)._get_conversion_rate(
                    rec.amount_currency_id, bill_currency, rec.service_job_id.company_id, rec.service_job_id.date
                ) if bill_currency else currency_exchange_rate or 1
            else:
                rec.bill_conversion_rate = rec.bill_conversion_rate or 1

    @api.depends('move_line_ids', 'move_line_ids.parent_state')
    def _compute_bill_currency_id(self):
        for rec in self:
            move_line_ids = rec.move_line_ids
            rec.bill_currency_id = move_line_ids and move_line_ids[0].move_id.currency_id.id or False

    @api.depends('total_currency_amount', 'bill_conversion_rate')
    def _compute_bill_currency_amount(self):
        for rec in self:
            invoice_conversion_rate = rec.amount_conversion_rate
            rec.bill_currency_amount = rec.total_currency_amount * (invoice_conversion_rate if rec.amount_currency_id != rec.company_id.currency_id else 1)

    @api.depends('bill_currency_amount', 'actual_billed_amount', 'bill_conversion_rate')
    def _compute_residual_amount(self):
        for rec in self:
            rec.amount_residual = rec.bill_currency_amount - rec.actual_billed_amount
            reverse_conversion_rate = 1/rec.amount_conversion_rate
            rec.amount_currency_residual = reverse_conversion_rate * rec.amount_residual
            rec.total_residual_amount = rec.amount_currency_residual * rec.amount_conversion_rate

    @api.depends('bill_currency_amount', 'move_line_ids', 'move_line_ids.amount_currency', 'move_line_ids.parent_state')
    def _compute_actual_billed_amount(self):
        for rec in self:
            service_job_move_lines = rec.move_line_ids.filtered(lambda m: m.parent_state != 'cancel')
            actual_billed_amount = abs(sum(service_job_move_lines.mapped('amount_currency')))
            if service_job_move_lines.mapped('currency_id') not in rec.company_id.currency_id:
                rec.actual_billed_amount = actual_billed_amount * rec.amount_conversion_rate
            else:
                rec.actual_billed_amount = actual_billed_amount  # Amount need to be in absolute

    @api.depends('amount_currency_residual', 'total_currency_amount', 'move_line_ids')
    def _compute_bill_status(self):
        for rec in self:
            status = 'no'
            move_line_ids = rec.move_line_ids
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

        self.check_charges_rate_per_unit('vendor bill')
        action = self.env.ref('fm_service_job_charges.service_job_charge_bill_wizard_action').sudo().read([])[0]
        cash_rounding_id = False
        if self.env.user.has_group('account.group_cash_rounding'):
            cash_rounding_id = self.env['account.cash.rounding'].search([], limit=1).id
        action['context'] = {
            'default_charge_ids': [(6, False, charges_to_bill.ids)],
            'default_currency_id': self.company_id.currency_id.id,
            'default_service_job_id': charges_to_bill[0].service_job_id.id,
            'default_invoice_cash_rounding_id': cash_rounding_id
        }
        return action

    def unlink(self):
        for rec in self:
            if rec.status in rec._modification_line_restrict_states():
                raise UserError(_("Charges that have been partially or fully billed cannot be deleted!"))
        return super().unlink()

    def _get_action_for_view_moves(self):
        move_type = self.env.context.get('move_type')
        if not move_type:
            return
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_refund_type" if move_type == 'in_refund' else 'account.action_move_in_invoice_type')
        action['context'] = {'default_service_job_id': self.id, 'default_move_type': move_type, 'create': 0, 'search_default_posted': 1}
        return action, move_type

    def action_open_moves(self):
        self.ensure_one()
        action, move_type = self._get_action_for_view_moves()
        if not move_type:
            return
        move_line_ids = self.move_line_ids
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
