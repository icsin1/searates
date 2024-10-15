# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProFormaInvoice(models.Model):
    _inherit = 'pro.forma.invoice'

    service_job_id = fields.Many2one('freight.service.job', copy=False, readonly=True)
    charge_service_job_ids = fields.Many2many('freight.service.job', 'service_job_proforma_invoice_rel', string=" Charge Service Job")  # in proforma invoice to link multiple service job
    show_service_job_charge_button = fields.Boolean(compute='_compute_show_service_job_charge_button', store=True)

    def _recompute_cash_rounding_lines(self):
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _compute_cash_rounding(self, total_amount_currency):
            difference = self.invoice_cash_rounding_id.compute_difference(self.currency_id, total_amount_currency)
            if self.currency_id == self.company_id.currency_id:
                diff_amount_currency = diff_balance = difference
            else:
                diff_amount_currency = difference
                if self.house_shipment_id:
                    currency_date = self.house_shipment_id.shipment_date
                elif self.service_job_id:
                    currency_date = self.service_job_id.date
                else:
                    currency_date = fields.Date.today()
                diff_balance = self.currency_id._convert(diff_amount_currency, self.company_id.currency_id, self.company_id, currency_date)
            return diff_balance, diff_amount_currency

        def _apply_cash_rounding(self, diff_balance, diff_amount_currency, cash_rounding_line):
            rounding_line_vals = {
                'quantity': 1.0,
                'pro_forma_invoice_id': self.id,
                'company_id': self.company_id.id,
                'company_currency_id': self.company_id.currency_id.id,
                'is_rounding_line': True,
                'price_unit': diff_amount_currency,
            }

            if self.invoice_cash_rounding_id.strategy == 'biggest_tax':
                biggest_tax_line = None
                for tax_line in self.line_ids.filtered('tax_repartition_line_id'):
                    if not biggest_tax_line or tax_line.price_subtotal > biggest_tax_line.price_subtotal:
                        biggest_tax_line = tax_line

                if not biggest_tax_line:
                    return

                rounding_line_vals.update({
                    'service_name': _('%s (rounding)', biggest_tax_line.name),
                    'account_id': biggest_tax_line.account_id.id,
                    'tax_repartition_line_id': biggest_tax_line.tax_repartition_line_id.id,
                    'tax_tag_ids': [(6, 0, biggest_tax_line.tax_tag_ids.ids)],
                    'exclude_from_invoice_tab': True,
                })

            elif self.invoice_cash_rounding_id.strategy == 'add_invoice_line':
                if diff_balance > 0.0 and self.invoice_cash_rounding_id.loss_account_id:
                    account_id = self.invoice_cash_rounding_id.loss_account_id.id
                else:
                    account_id = self.invoice_cash_rounding_id.profit_account_id.id
                rounding_line_vals.update({
                    'service_name': self.invoice_cash_rounding_id.name,
                    'account_id': account_id,
                })

            if cash_rounding_line:
                cash_rounding_line.update({
                    'account_id': rounding_line_vals['account_id'],
                })
            else:
                create_method = in_draft_mode and self.env['pro.forma.invoice.line'].new or self.env['pro.forma.invoice.line'].create
                cash_rounding_line = create_method(rounding_line_vals)

        existing_cash_rounding_line = self.pro_forma_invoice_line_ids.filtered(lambda line: line.is_rounding_line)

        if not self.invoice_cash_rounding_id:
            self.pro_forma_invoice_line_ids -= existing_cash_rounding_line
            return

        if self.invoice_cash_rounding_id and existing_cash_rounding_line:
            strategy = self.invoice_cash_rounding_id.strategy
            old_strategy = 'add_invoice_line'
            if strategy != old_strategy:
                self.pro_forma_invoice_line_ids -= existing_cash_rounding_line
                existing_cash_rounding_line = self.env['pro.forma.invoice.line']

        others_lines = self.pro_forma_invoice_line_ids.filtered(lambda line: not line.is_rounding_line)
        others_lines -= existing_cash_rounding_line
        total_amount_currency = (sum(others_lines.mapped('price_subtotal')) + sum(others_lines.mapped('price_tax')))

        diff_balance, diff_amount_currency = _compute_cash_rounding(self, total_amount_currency)

        if self.currency_id.is_zero(diff_balance) and self.currency_id.is_zero(diff_amount_currency):
            self.pro_forma_invoice_line_ids -= existing_cash_rounding_line
            return

        _apply_cash_rounding(self, diff_balance, diff_amount_currency, existing_cash_rounding_line)

    def action_create_invoice(self):
        self.ensure_one()
        if self.service_job_id:
            self.action_create_invoice_service_job()
        else:
            return super().action_create_invoice()

    def action_create_invoice_service_job(self):
        self.ensure_one()
        if not self.service_job_id:
            return
        move_type = 'out_invoice'
        AccountMove = self.env['account.move'].with_context(default_move_type=move_type)
        move_id = AccountMove.create(self._prepare_invoice_service_job(move_type))
        move_id.with_context(skip_reset_line=True)._onchange_partner_id()
        self.write({'state': 'invoiced'})
        return self.action_view_invoice(move_id)

    def _prepare_invoice_service_job(self, move_type):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_move_type=move_type)
        invoice_ref = '{} - {}'.format(self.name, self.service_job_id.booking_nomination_no)
        return {
            'move_type': move_type,
            'currency_id': self.currency_id.id,
            'user_id': self.env.user.id,
            'invoice_user_id': self.env.user.id,
            'partner_id': self.partner_id.id,
            'journal_id': AccountMove._get_default_journal().id,
            'invoice_origin': invoice_ref,
            'company_id': self.company_id.id,
            'ref': invoice_ref,
            'booking_reference': invoice_ref,
            'invoice_incoterm_id': self.service_job_id and self.service_job_id.service_job_quote_id and self.service_job_id.service_job_quote_id.incoterm_id.id,
            'invoice_line_ids': self._prepare_invoice_line_service_job(),
            'invoice_date': fields.Date.context_today(self),
            'from_shipment_charge': False,
            'pro_forma_invoice_id': self.id,
            'add_charges_from': 'job',
            'charge_service_job_ids': [(6, 0, self.charge_service_job_ids.ids or self.service_job_id.ids)],   # from pro forma multiple service job has to be linked in Invoice
            'invoice_cash_rounding_id': self.invoice_cash_rounding_id.id if self.invoice_cash_rounding_id else False,
        }

    def _prepare_invoice_line_service_job(self):
        self.ensure_one()
        invoice_lines = []
        pro_forma_invoice_line_ids = self.pro_forma_invoice_line_ids
        if self.invoice_cash_rounding_id:
            pro_forma_invoice_line_ids = self.pro_forma_invoice_line_ids.filtered(lambda line: not line.is_rounding_line)

        for pro_forma_line in pro_forma_invoice_line_ids:
            invoice_lines.append((0, 0, {
                'name': pro_forma_line.service_name,
                'product_id': pro_forma_line.product_id.id,
                'product_uom_id': pro_forma_line.product_uom_id.id,
                'quantity': pro_forma_line.quantity,
                'price_unit': pro_forma_line.price_unit,
                'tax_ids': [(6, 0, pro_forma_line.tax_ids.ids)],
                'service_job_charge_revenue_id': pro_forma_line.service_job_charge_revenue_id.id,
                'account_id': pro_forma_line.service_job_charge_revenue_id.property_account_id.id,
                'currency_exchange_rate': pro_forma_line.currency_exchange_rate,
                'shipment_charge_currency_id': pro_forma_line.shipment_charge_currency_id.id,
                'charge_rate_per_unit': pro_forma_line.charge_rate_per_unit
            }))
        return invoice_lines

    def add_charges_from_service_job(self):
        self.ensure_one()
        pro_forma_invoice_lines = []
        self.remove_pro_forma_charge_lines()
        service_job_charge_invoice_wizard_ids = self.env['service.job.charge.pro.forma.invoice.wizard']
        to_pro_forma_invoice = False
        for service_job_id in self.charge_service_job_ids:
            to_pro_forma_invoice = service_job_id.revenue_charge_ids.filtered(lambda charge: charge.status in ['no', 'pro_forma_cancel'])
            if not to_pro_forma_invoice:
                continue
            service_job_charge_invoice_wizard_ids |= self._create_service_job_revenue_invoice_wizard(service_job_id, to_pro_forma_invoice)

        for wizard_line_id in service_job_charge_invoice_wizard_ids.line_ids:
            pro_forma_invoice_lines += wizard_line_id._prepare_pro_forma_invoice_line()

        self.write({'pro_forma_invoice_line_ids': pro_forma_invoice_lines})
        self._recompute_cash_rounding_lines()

    def _create_service_job_revenue_invoice_wizard(self, service_job_id, charges):
        self.ensure_one()
        record = self.env['service.job.charge.pro.forma.invoice.wizard'].create({
            'charge_ids': [(6, False, charges.ids)],
            'service_job_id': service_job_id.id,
            'partner_mode': 'specific',
            'partner_ids': [(6, 0, self.partner_id.ids)],
            'single_currency_billing': True,
            'currency_id': self.currency_id.id,
            'invoice_cash_rounding_id': self.invoice_cash_rounding_id.id
        })
        record._onchange_field_values()
        record._onchange_currency_id()
        return record

    @api.depends('charge_service_job_ids', 'state')
    def _compute_show_service_job_charge_button(self):
        for rec in self:
            rec.show_service_job_charge_button = rec.charge_service_job_ids and rec.state == 'to_approve'


class ProFormaInvoiceLine(models.Model):
    _inherit = 'pro.forma.invoice.line'

    service_job_charge_revenue_id = fields.Many2one('service.job.charge.revenue', copy=False)
