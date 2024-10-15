from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShipmentChargeProFormaInvoiceWizard(models.TransientModel):
    _name = 'shipment.charge.pro.forma.invoice.wizard'
    _inherit = 'journal.entry.generate.wizard.mixin'
    _description = 'Wizard Pro Forma Invoices'

    @api.depends('single_currency_billing', 'house_shipment_id', 'currency_id')
    def _compute_show_exchange_rate(self):
        for rec in self:
            is_shipment_currency_charge = all(c.amount_currency_id.id == rec.currency_id.id for c in rec.charge_ids)
            rec.show_exchange_rate = True if rec.single_currency_billing and rec.house_shipment_id.currency_id.id != rec.currency_id.id and not is_shipment_currency_charge else False

    house_shipment_id = fields.Many2one('freight.house.shipment', ondelete='cascade')
    partner_mode = fields.Selection(string='Invoice To Customers')
    charge_ids = fields.Many2many('house.shipment.charge.revenue', 'charge_pro_forma_invoice_wizard_charge_rel', 'wizard_id', 'charge_id', string='Charges',
                                  domain="[('house_shipment_id', '=', house_shipment_id), ('status', 'not in', ['pro_forma', 'partial', 'fully_invoiced'])]")
    line_ids = fields.One2many('shipment.charge.pro.forma.invoice.wizard.line', 'wizard_id', string='Invoice Lines')
    filter_partner_ids = fields.Many2many('res.partner', compute='_compute_filter_partner_ids')
    show_exchange_rate = fields.Boolean(string='Show Exchange Rate', compute='_compute_show_exchange_rate', store=False)
    invoice_cash_rounding_id = fields.Many2one('account.cash.rounding', string='Cash Rounding Method')

    @api.depends('house_shipment_id')
    def _compute_filter_partner_ids(self):
        for rec in self:
            partners = rec.house_shipment_id.shipment_partner_ids.filtered(lambda p: not p.partner_type_id.is_vendor).mapped('partner_id')
            rec.filter_partner_ids = [(6, False, partners.ids)]

    @api.onchange('partner_mode', 'single_currency_billing', 'partner_ids', 'charge_ids', 'currency_id', 'amount_conversion_rate')
    def _onchange_field_values(self):
        self._ensure_currency_for_charge_lines()
        self._auto_set_invoice_currency()
        self.action_generate_pro_forma_invoice_lines()

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        for rec in self.filtered(lambda r: r.currency_id):
            rec.amount_conversion_rate = 1 / (self.currency_id._get_conversion_rate(
                rec.house_shipment_id.currency_id, rec.currency_id, rec.house_shipment_id.company_id, rec.house_shipment_id.shipment_date) or 1.0)

    def get_exchange_rate(self, charge):
        self.ensure_one()
        if self.single_currency_billing and self.currency_id.id != charge.amount_currency_id.id and charge.amount_currency_id.id == self.house_shipment_id.currency_id.id:
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

    @api.onchange('single_currency_billing', 'currency_id', 'charge_ids')
    @api.constrains('single_currency_billing', 'currency_id')
    def _check_charge_billing_currency(self):
        for rec in self.filtered(lambda r: r.currency_id):
            charges_currency_names = rec.charge_ids.mapped('amount_currency_id.name')
            shipment_currency = rec.house_shipment_id.currency_id
            is_shipment_currency_charge = all(c.amount_currency_id.id == shipment_currency.id for c in rec.charge_ids)
            if shipment_currency.name in charges_currency_names:
                charges_currency_names.remove(shipment_currency.name)
            charge_shipment_currency_names = charges_currency_names + [shipment_currency.name]
            if rec.single_currency_billing and not is_shipment_currency_charge:
                # rec.currency_id.id != shipment_currency.id:
                if len(charges_currency_names) > 1 and rec.currency_id.id != shipment_currency.id:
                    raise ValidationError(_('For different currency-charges Invoice-currency must be %s to generate Invoice.') % (shipment_currency.name))
                if len(charges_currency_names) == 1 and rec.currency_id.name not in charge_shipment_currency_names:
                    raise ValidationError(_('Invoice Currency can be %s only.') % (', '.join(charge_shipment_currency_names)))

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

    def action_generate_pro_forma_invoice_lines(self):
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
                currency_charges = partner_charges.filtered_domain([('amount_currency_id', '=', currency.id)]) if not self.single_currency_billing else partner_charges
                total_amount = 0

                for charge in currency_charges:
                    currency_exchange_rate = self.get_exchange_rate(charge)
                    charge.with_context(currency_exchange_rate=currency_exchange_rate)._compute_invoice_conversion_rate()
                    converted_amount = charge.amount_currency_id.with_context(currency_exchange_rate=currency_exchange_rate)._convert(
                        charge.total_currency_amount, currency, charge.house_shipment_id.company_id, charge.house_shipment_id.shipment_date
                    )
                    total_amount += converted_amount

                if total_amount:
                    lines.append((0, 0, {
                        'partner_id': partner.id,
                        'currency_id': currency.id,
                        'no_of_charges': len(currency_charges),
                        'charge_ids': [(6, False, currency_charges.ids)],
                        'amount': total_amount,
                    }))
        self.line_ids = [(6, False, [])] + lines

    def action_generate_pro_forma_invoices(self):
        pro_forma_invoices = []
        for line in self.line_ids:
            pro_forma_invoices.append(line._prepare_pro_forma_invoice())
        pro_forma_invoice = self.env['pro.forma.invoice'].create(pro_forma_invoices)
        for invoice in pro_forma_invoice:
            invoice._onchange_recompute_dynamic_lines()
        return self.env['house.shipment.charge.revenue'].view_pro_forma_invoice(pro_forma_invoice)

    def action_view_pro_forma_invoice(self, pro_forma_invoice_ids):
        action = self.env["ir.actions.actions"]._for_xml_id("fm_proforma.pro_forma_invoice_action")
        action['context'] = {'create': 0}
        if len(pro_forma_invoice_ids) > 1:
            action['domain'] = [('id', 'in', pro_forma_invoice_ids.ids)]
            return action

        form_view = [(self.env.ref('fm_proforma.pro_forma_invoice_view_form').id, 'form')]
        action['views'] = form_view + [(state, view) for state, view in action.get('views', []) if view != 'form']
        action['res_id'] = pro_forma_invoice_ids.id
        return action


class ShipmentChargeProFormaInvoiceWizardLine(models.TransientModel):
    _name = 'shipment.charge.pro.forma.invoice.wizard.line'
    _inherit = 'journal.entry.generate.wizard.line.mixin'
    _description = 'Generate Pro-Forma Lines'

    wizard_id = fields.Many2one('shipment.charge.pro.forma.invoice.wizard', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Customer')
    currency_id = fields.Many2one('res.currency', string="Currency")
    charge_ids = fields.Many2many('house.shipment.charge.revenue', 'charge_pro_forma_invoice_line_wizard_charge_rel', 'wizard_id', 'charge_id', string='Charges')

    def _prepare_pro_forma_invoice(self):
        self.ensure_one()
        house_shipment = self.wizard_id.house_shipment_id
        invoice_cash_rounding_id = self.wizard_id.invoice_cash_rounding_id
        pro_forma_invoice_vals = {
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'company_id': house_shipment.company_id.id,
            'house_shipment_id': house_shipment.id,
            'charge_house_shipment_ids': [(6, 0, self.mapped('charge_ids').mapped(
                'house_shipment_id').ids or self.wizard_id.house_shipment_id.ids)],  # fro
            'pro_forma_invoice_line_ids': self._prepare_pro_forma_invoice_line(),
            'invoice_cash_rounding_id': invoice_cash_rounding_id.id if invoice_cash_rounding_id else False
        }
        return pro_forma_invoice_vals

    def _prepare_pro_forma_invoice_line(self):
        self.ensure_one()
        charge_lines = []
        for charge in self.charge_ids:
            currency_exchange_rate = self.wizard_id.get_exchange_rate(charge)
            line_currency_exchange_rate = self.wizard_id.get_invoice_bill_line_exchange_rate(charge)
            charge_amount = charge.amount_currency_id.with_context(
                currency_exchange_rate=currency_exchange_rate)._convert(charge.amount_currency_residual, self.currency_id, charge.house_shipment_id.company_id, charge.house_shipment_id.shipment_date)
            charge_ratio = charge_amount / self.amount
            # Charge rate converted to requested currency
            charge_rate = charge.amount_currency_id.with_context(
                currency_exchange_rate=currency_exchange_rate)._convert(charge.amount_rate, self.currency_id, charge.house_shipment_id.company_id, charge.house_shipment_id.shipment_date)

            # As amount is total of all charges
            # Getting value of amount based on charge ratio
            amount_for_charge = self.amount * charge_ratio
            fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(charge.partner_id.id)
            taxes = fiscal_position.map_tax(charge.tax_ids)
            charge_lines.append((0, 0, {
                'service_name': charge.charge_description,
                'product_id': charge.product_id.id,
                'product_uom_id': charge.product_id.uom_id.id,
                'quantity': round(amount_for_charge / charge_rate, 3),  # decreasing quantity as rate can be fixed
                'sell_currency_id': self.currency_id.id,
                'price_unit': charge_rate,
                'tax_ids': [(6, 0, taxes.ids)],
                'house_shipment_charge_revenue_id': charge.id,
                'currency_exchange_rate': line_currency_exchange_rate,
                'shipment_charge_currency_id': charge.amount_currency_id.id,
                'charge_rate_per_unit': charge.amount_rate
            }))
        return charge_lines
