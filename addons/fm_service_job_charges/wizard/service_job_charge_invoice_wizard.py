from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceJobChargeInvoiceWizard(models.TransientModel):
    _name = 'service.job.charge.invoice.wizard'
    _inherit = 'journal.entry.generate.wizard.mixin'
    _description = 'Generating Invoices'

    @api.depends('single_currency_billing', 'service_job_id', 'currency_id')
    def _compute_show_exchange_rate(self):
        for rec in self:
            is_service_job_currency_charge = all(c.amount_currency_id.id == rec.currency_id.id for c in rec.charge_ids)
            rec.show_exchange_rate = True if rec.single_currency_billing and rec.service_job_id.currency_id.id != rec.currency_id.id and not is_service_job_currency_charge else False

    service_job_id = fields.Many2one('freight.service.job', ondelete='cascade')
    partner_mode = fields.Selection(string='Invoice To Customers')
    charge_ids = fields.Many2many(
        'service.job.charge.revenue', 'service_charge_invoice_wizard_charge_rel', 'wizard_id', 'charge_id', string='Charges',
        domain="[('service_job_id', '=', service_job_id), ('status', 'not in', ['pro_forma', 'pro_forma_cancel', 'fully_invoiced'])]")
    line_ids = fields.One2many('service.job.charge.invoice.wizard.line', 'wizard_id', string='Invoice Lines')
    filter_partner_ids = fields.Many2many('res.partner', compute='_compute_filter_partner_ids')
    is_partial_invoice = fields.Boolean(compute='_compute_is_partial_invoice', store=True)
    show_exchange_rate = fields.Boolean(string='Show Exchange Rate', compute='_compute_show_exchange_rate', store=False)
    invoice_cash_rounding_id = fields.Many2one('account.cash.rounding', string='Cash Rounding Method')

    @api.depends('line_ids', 'line_ids.is_partial_invoice')
    def _compute_is_partial_invoice(self):
        for rec in self:
            rec.is_partial_invoice = any(rec.line_ids.mapped('is_partial_invoice'))

    @api.depends('service_job_id')
    def _compute_filter_partner_ids(self):
        for rec in self:
            partners = rec.service_job_id.service_job_partner_ids.filtered(lambda p: not p.partner_type_id.is_vendor).mapped('partner_id')
            rec.filter_partner_ids = [(6, False, partners.ids)]

    @api.onchange('partner_mode', 'single_currency_billing', 'partner_ids', 'charge_ids', 'currency_id', 'amount_conversion_rate')
    def _onchange_field_values(self):
        self._ensure_currency_for_charge_lines()
        self._auto_set_invoice_currency()
        self.action_generate_invoice_lines()

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        for rec in self.filtered(lambda r: r.currency_id):
            rec.amount_conversion_rate = 1 / (self.currency_id._get_conversion_rate(
                rec.service_job_id.currency_id, rec.currency_id, rec.service_job_id.company_id, rec.service_job_id.date) or 1.0)

    def get_exchange_rate(self, charge):
        self.ensure_one()
        if self.single_currency_billing and self.currency_id.id != charge.amount_currency_id.id and charge.amount_currency_id.id == self.service_job_id.currency_id.id:
            currency_exchange_rate = self.amount_conversion_rate
        else:
            currency_exchange_rate = charge.amount_conversion_rate
        return currency_exchange_rate or 1

    def get_invoice_bill_line_exchange_rate(self, charge_id):
        self.ensure_one()
        if self.single_currency_billing and self.currency_id.id != charge_id.amount_currency_id.id:
            if self.show_exchange_rate and self.amount_conversion_rate:
                conversion_rate = (1 / self.amount_conversion_rate)
            else:
                conversion_rate = charge_id.amount_conversion_rate
        else:
            conversion_rate = charge_id.amount_conversion_rate

        if not self.single_currency_billing or charge_id.amount_currency_id.id == self.currency_id.id:
            currency_exchange_rate = 1
        else:
            currency_exchange_rate = conversion_rate

        return currency_exchange_rate

    @api.constrains('single_currency_billing', 'currency_id', 'charge_ids', 'amount_conversion_rate')
    def _check_partial_invoice_currency_rate(self):
        for rec in self:
            for charge in rec.charge_ids.filtered(lambda c: c.status == 'partial'):
                to_invoice_currency = rec.currency_id if rec.single_currency_billing else charge.amount_currency_id
                to_invoice_rate = charge.amount_currency_id.with_context(currency_exchange_rate=rec.get_exchange_rate(charge))._get_conversion_rate(
                    charge.amount_currency_id, to_invoice_currency, self.service_job_id.company_id, self.service_job_id.date)
                if charge.invoice_currency_id.id != to_invoice_currency.id:
                    raise ValidationError(_('Invoice currency must be %s because charge is Partially invoiced.') % (charge.invoice_currency_id.name))
                if round(charge.invoice_conversion_rate, 3) != round(to_invoice_rate, 3):
                    raise ValidationError(_('Currency Rate must not be changed because charge is Partially invoiced.'))

    @api.onchange('single_currency_billing', 'currency_id', 'charge_ids')
    @api.constrains('single_currency_billing', 'currency_id')
    def _check_charge_billing_currency(self):
        for rec in self.filtered(lambda r: r.currency_id):
            charges_currency_names = rec.charge_ids.mapped('amount_currency_id.name')
            service_job = rec.service_job_id.currency_id
            is_service_job_charge = all(c.amount_currency_id.id == service_job.id for c in rec.charge_ids)
            if service_job.name in charges_currency_names:
                charges_currency_names.remove(service_job.name)
            charge_service_job_names = charges_currency_names + [service_job.name]
            if rec.single_currency_billing and not is_service_job_charge:
                # rec.currency_id.id != service_job.id:
                if len(charges_currency_names) > 1 and rec.currency_id.id != service_job.id:
                    raise ValidationError(_('For different currency-charges Invoice-currency must be %s to generate Invoice.') % (service_job.name))
                if len(charges_currency_names) == 1 and rec.currency_id.name not in charge_service_job_names:
                    raise ValidationError(_('Invoice Currency can be %s only.') % (', '.join(charge_service_job_names)))

    def _ensure_currency_for_charge_lines(self):
        self.ensure_one()
        invoice_currencies = self.charge_ids.mapped('invoice_currency_id')
        if len(invoice_currencies) > 1:
            charge_line_currencies = ['Charge "{}" of "{}" currency already created'.format(
                charge.display_name,
                charge.invoice_currency_id.name
            ) for charge in self.charge_ids]
            raise ValidationError(_('You can not club invoices of different currency which are already partially invoiced\n\n{}'.format(
                '.\n'.join(charge_line_currencies)
            )))

    def _auto_set_invoice_currency(self):
        """ Auto enabling single currency invoice based on invoice currency incase of
            amount currency is different and invoice currency is only single
        """
        for rec in self:
            invoice_currency = self.charge_ids.mapped('invoice_currency_id')
            amount_currency = self.charge_ids.mapped('amount_currency_id')
            if len(amount_currency) > 1 and invoice_currency and len(invoice_currency) == 1:
                rec.single_currency_billing = True
                rec.currency_id = invoice_currency.id

    def action_generate_invoice_lines(self):
        for rec in self:
            rec._generate_grouping_lines()

    def _generate_grouping_lines(self):
        self.ensure_one()
        lines = []

        partners = self.charge_ids.mapped('partner_id') if self.partner_mode == 'all' else self.partner_ids
        for partner in partners:
            partner_charges = self.charge_ids.filtered_domain([('partner_id', '=', partner._origin.id)])
            currencies = partner_charges.mapped('amount_currency_id') if not self.single_currency_billing else self.currency_id
            for currency in currencies:
                currency_charges = partner_charges.filtered_domain([('amount_currency_id', '=', currency.id)])\
                    if not self.single_currency_billing else partner_charges.filtered_domain([('partner_id', '=', partner._origin.id)])
                total_amount = 0
                for charge in currency_charges:
                    currency_exchange_rate = self.get_exchange_rate(charge)
                    charge.with_context(currency_exchange_rate=currency_exchange_rate)._compute_invoice_conversion_rate()
                    converted_amount = charge.amount_currency_id.with_context(currency_exchange_rate=currency_exchange_rate)._convert(
                        charge.amount_currency_residual, currency, self.service_job_id.company_id, self.service_job_id.date, round=False
                    )
                    total_amount += converted_amount
                if total_amount:
                    lines.append((0, 0, {
                        'partner_id': partner.id,
                        'currency_id': currency.id,
                        'no_of_charges': len(currency_charges),
                        'charge_ids': [(6, False, currency_charges.ids)],
                        'amount': total_amount,
                        'full_amount': total_amount
                    }))
        self.line_ids = [(6, False, [])] + lines

    def action_generate_invoices(self):
        move_type = 'out_invoice'
        invoices = []
        for line in self.line_ids:
            invoices.append(line._generate_invoice(move_type))
        AccountMove = self.env['account.move'].with_context(default_move_type=move_type)
        moves = AccountMove.create(invoices)
        # Force on change partner
        for move in moves:
            move.with_context(skip_reset_line=True)._onchange_partner_id()
        return self.action_view_invoice(moves, move_type)

    def action_view_invoice(self, invoices, move_type):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type" if move_type != "in_invoice" else "account.action_move_in_invoice_type")
        action['context'] = {'create': 0}
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
            return action

        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        action['views'] = form_view + [(state, view) for state, view in action.get('views', []) if view != 'form']
        action['res_id'] = invoices.id
        return action


class ServiceJobChargeInvoiceWizardLine(models.TransientModel):
    _name = 'service.job.charge.invoice.wizard.line'
    _inherit = 'journal.entry.generate.wizard.line.mixin'
    _description = 'Invoice Lines'

    wizard_id = fields.Many2one('service.job.charge.invoice.wizard', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Invoice To')
    currency_id = fields.Many2one('res.currency', string="Invoice Currency")
    charge_ids = fields.Many2many('service.job.charge.revenue', 'service_charge_invoice_line_wizard_charge_rel', 'wizard_id', 'charge_id', string='Charges')

    def _generate_invoice(self, move_type):
        self.ensure_one()
        service_job = self.wizard_id.service_job_id
        AccountMove = self.env['account.move'].with_context(default_move_type=move_type, default_company_id=service_job.company_id.id)  # Keep Service-Job company to get journal
        invoice_cash_rounding_id = self.wizard_id.invoice_cash_rounding_id
        return {
            'move_type': move_type,
            'currency_id': self.currency_id.id,
            'user_id': self.env.user.id,
            'invoice_user_id': self.env.user.id,
            'partner_id': self.partner_id.id,
            'journal_id': AccountMove._get_default_journal().id,
            'invoice_origin': service_job.booking_nomination_no,
            'company_id': service_job.company_id.id,
            'ref': service_job.booking_nomination_no,
            'invoice_line_ids': self._prepare_invoice_line(move_type),
            'invoice_date': fields.Date.context_today(self),
            'from_shipment_charge': True,
            'add_charges_from': 'job',
            'charge_service_job_ids': [(6, 0, self.wizard_id.service_job_id.ids)],
            'invoice_cash_rounding_id': invoice_cash_rounding_id.id if invoice_cash_rounding_id else False
        }

    def _prepare_invoice_line(self, move_type):
        self.ensure_one()
        charge_lines = []
        for charge in self.charge_ids:
            currency_exchange_rate = self.wizard_id.get_exchange_rate(charge)
            charge_amount = (charge.amount_currency_id.with_context(currency_exchange_rate=currency_exchange_rate).
                             _convert(charge.amount_currency_residual, self.currency_id, charge.service_job_id.company_id,
                                      charge.service_job_id.date, round=False))
            charge_ratio = charge_amount / (self.full_amount or 1)
            # Charge rate converted to requested currency
            charge_rate = (charge.amount_currency_id.with_context(currency_exchange_rate=currency_exchange_rate).
                           _convert(charge.amount_rate, self.currency_id, charge.service_job_id.company_id,
                                    charge.service_job_id.date, round=False) or 1)
            # As amount is total of all charges
            # Getting value of amount based on charge ratio
            amount_for_charge = self.amount * charge_ratio
            quantity = amount_for_charge / charge_rate if self.is_partial_invoice or charge.status == 'partial' else charge.quantity  # decreasing quantity for partial-invoice as rate can be fixed
            fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(charge.partner_id.id)
            taxes = fiscal_position.map_tax(charge.tax_ids)
            charge_lines.append((0, 0, {
                'name': '{}'.format(charge.charge_description),
                'product_id': charge.product_id.id,
                'product_uom_id': charge.product_id.uom_id.id,
                'quantity': quantity,
                'price_unit': charge_rate,
                'tax_ids': [(6, 0, taxes.ids)],
                'service_job_charge_revenue_id': charge.id,
                'account_id': charge.property_account_id.id,
                'shipment_charge_currency_id': charge.amount_currency_id.id
            }))
        return charge_lines
