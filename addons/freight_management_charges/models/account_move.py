# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_reconciled_vals(self, partial, amount, counterpart_line):
        if counterpart_line.move_id.ref:
            reconciliation_ref = '%s (%s)' % (counterpart_line.move_id.name, counterpart_line.move_id.ref)
        else:
            reconciliation_ref = counterpart_line.move_id.name
        return {
            'name': counterpart_line.name,
            'journal_name': counterpart_line.journal_id.name,
            'amount': amount,
            'currency': self.currency_id.symbol,
            'digits': [69, self.currency_id.decimal_places],
            'position': self.currency_id.position,
            'date': partial.max_date,
            'payment_id': counterpart_line.id,
            'partial_id': partial.id,
            'account_payment_id': counterpart_line.payment_id.id,
            'payment_method_name': counterpart_line.payment_id.payment_method_line_id.name,
            'move_id': counterpart_line.move_id.id,
            'ref': reconciliation_ref,
        }

    @api.depends('partner_id')
    def _compute_allowed_house_shipment_ids(self):
        HouseRevenueCharge = self.env['house.shipment.charge.revenue']
        HouseCostCharge = self.env['house.shipment.charge.cost']
        for move in self:
            allowed_house_shipment_ids = []
            if move.move_type == "out_invoice":
                charge_ids = HouseRevenueCharge.search([('partner_id', '=', move.partner_id.id), ('status', 'in', ('no', 'partial')), ('company_id', '=', move.company_id.id)])
                allowed_house_shipment_ids = [(6, 0, charge_ids.mapped('house_shipment_id.id'))]
            if move.move_type == "in_invoice":
                charge_ids = HouseCostCharge.search([('partner_id', '=', move.partner_id.id), ('status', 'in', ('no', 'partial')), ('company_id', '=', move.company_id.id)])
                allowed_house_shipment_ids = [(6, 0, charge_ids.mapped('house_shipment_id.id'))]
            move.allowed_house_shipment_ids = allowed_house_shipment_ids

    @api.depends('partner_id')
    def _compute_allowed_master_shipment_ids(self):
        MasterCostCharge = self.env['master.shipment.charge.cost']
        for move in self:
            allowed_master_shipment_ids = []
            if move.move_type == "in_invoice":
                charge_ids = MasterCostCharge.search(
                    [('partner_id', '=', move.partner_id.id),
                     ('has_bill', '=', False),
                     ('status', '=', 'adjusted'),
                     ('company_id', '=', move.company_id.id)])
                allowed_master_shipment_ids = [(6, 0, charge_ids.mapped('master_shipment_id.id'))]
            move.allowed_master_shipment_ids = allowed_master_shipment_ids

    from_shipment_charge = fields.Boolean(copy=False)
    charge_house_shipment_ids = fields.Many2many('freight.house.shipment', 'house_account_move_rel', string="Charge House Shipment")
    charge_master_shipment_ids = fields.Many2many('freight.master.shipment', 'master_account_move_rel', string="Charge Master Shipment")
    allowed_house_shipment_ids = fields.Many2many('freight.house.shipment', 'allowed_house_shipment_account_move_rel',
                                                  compute="_compute_allowed_house_shipment_ids")
    allowed_master_shipment_ids = fields.Many2many('freight.master.shipment', 'allowed_master_shipment_account_move_rel',
                                                   compute="_compute_allowed_master_shipment_ids")
    house_shipment_ids = fields.Many2many('freight.house.shipment', compute="_compute_house_shipment", store=True)
    master_shipment_ids = fields.Many2many('freight.master.shipment', 'freight_master_shipment_account_move_rel', compute="_compute_master_shipment", store=True)
    invoice_total = fields.Monetary(compute="_compute_invoice_total")
    credit_total = fields.Monetary(compute="_compute_credit_total")
    debit_total = fields.Monetary(compute="_compute_debit_total")
    bill_total = fields.Monetary(compute="_compute_bill_total")
    allowed_invoice_bill_moves = fields.Many2many('account.move', 'invoice_credit_moves_rel', compute='_compute_allowed_invoice_bill_moves')
    invoice_id = fields.Many2one('account.move', string="Invoice", help="It helps to fetch the invoice line and add into the credit note")
    add_charges_from = fields.Selection([('house', 'House'), ('master', 'Master')])
    booking_reference = fields.Char(string='Booking Reference', copy=False, tracking=True)

    @api.onchange('add_charges_from')
    def _onchange_add_charges_from(self):
        if self.add_charges_from == 'master' and self.move_type == 'in_invoice':
            self.charge_house_shipment_ids = [(5, 0, 0)]
        if self.add_charges_from == 'house':
            self.charge_master_shipment_ids = [(5, 0, 0)]
        if self.add_charges_from == "master" and self.move_type != "in_invoice":
            self.add_charges_from = 'house'
            return {
                'warning': {
                    'title': _("Warning"),
                    'message': _("The functionality for loading Master charges is available only for vendor bills.")
                }
            }

    def action_open_house_shipment(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('freight_management.freight_shipment_house_action')
        if len(self.house_shipment_ids) > 1:
            action['domain'] = [('id', 'in', self.house_shipment_ids.ids)]
            return action

        form_view = [(self.env.ref('freight_management.freight_house_shipment_view_form').id, 'form')]
        action['views'] = form_view + [(state, view) for state, view in action.get('views', []) if view != 'form']
        action['res_id'] = self.house_shipment_ids.id
        return action

    @api.depends('invoice_line_ids', 'invoice_line_ids.house_shipment_id')
    def _compute_house_shipment(self):
        self = self.with_context({'skip_line_updates': True})
        for rec in self:
            house_shipment_ids = rec.invoice_line_ids.mapped('house_shipment_id') | rec.invoice_line_ids.mapped('master_shipment_id').house_shipment_ids
            rec.house_shipment_ids = [(6, 0, house_shipment_ids.ids)]

    @api.depends('house_shipment_ids', 'house_shipment_ids.parent_id', 'charge_house_shipment_ids', 'charge_house_shipment_ids.parent_id', 'charge_master_shipment_ids')
    def _compute_master_shipment(self):
        self = self.with_context({'skip_line_updates': True})
        for rec in self:
            master_shipment_ids = []
            if rec.move_type == 'out_invoice':
                mbl_number = rec.house_shipment_ids.sudo().mapped('parent_id')
                master_shipment_ids = mbl_number.ids
            elif rec.move_type == 'in_invoice':
                if rec.charge_master_shipment_ids:
                    mbl_number = rec.charge_master_shipment_ids.sudo()
                else:
                    mbl_number = rec.house_shipment_ids.sudo().mapped('parent_id')
                master_shipment_ids = mbl_number.ids
            elif rec.move_type == 'out_refund':
                mbl_number = rec.house_shipment_ids.sudo().mapped('parent_id')
                master_shipment_ids = mbl_number.ids
            elif rec.move_type == 'in_refund':
                if rec.charge_master_shipment_ids:
                    mbl_number = rec.charge_master_shipment_ids.sudo()
                else:
                    mbl_number = rec.house_shipment_ids.sudo().mapped('parent_id')
                master_shipment_ids = mbl_number.ids
            rec.master_shipment_ids = [(6, 0, master_shipment_ids)]

    def _compute_invoice_total(self):
        for move in self:
            if move.move_type == 'out_refund':
                move.invoice_total = move.reversed_entry_id.amount_total_in_currency_signed
            else:
                move.invoice_total = 0

    def _compute_credit_total(self):
        for move in self:
            if move.move_type == 'out_invoice':
                domain = [('reversed_entry_id', '=', move.id)]
                move.credit_total = sum(move.search(domain).mapped('amount_total_in_currency_signed'))
            else:
                move.credit_total = 0

    def _compute_debit_total(self):
        for move in self:
            if move.move_type == 'in_invoice':
                domain = [('reversed_entry_id', '=', move.id)]
                move.debit_total = sum(move.search(domain).mapped('amount_total_in_currency_signed'))
            else:
                move.debit_total = 0

    def _compute_bill_total(self):
        for move in self:
            if move.move_type == 'in_refund':
                move.bill_total = move.reversed_entry_id.amount_total_in_currency_signed
            else:
                move.bill_total = 0

    @api.model_create_single
    def create(self, vals):
        move = super().create(vals)
        if move.partner_id and move.move_type in ['in_invoice', 'in_refund']:
            move.partner_id.update_vendor_tag()
        return move

    def copy(self, default=None):
        move_type_mapping = {'out_invoice': 'Customer Invoice', 'in_invoice': 'Vendor Bill'}
        if self.move_type in ('out_invoice', 'in_invoice') and self.add_charges_from:
            raise UserError("You cannot duplicate %s with %s charges." % (move_type_mapping[self.move_type], str(self.add_charges_from).title()))
        return super(AccountMove, self).copy(default)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        result = super(AccountMove, self)._onchange_partner_id()
        if self.partner_id:
            self.invoice_user_id = self.partner_id.user_id.id or self.env.user.id
        if self.state == 'draft' and not self._context.get('skip_reset_line'):
            self.charge_house_shipment_ids = [(5, 0, 0)]
            self.invoice_line_ids = [(5, 0, 0)]
            self.line_ids = [(5, 0, 0)]
            self.charge_master_shipment_ids = [(5, 0, 0)]
            self.payment_reference = ''
            self.ref = ''
            self.add_charges_from = ''
            self.invoice_date = ''
            self.invoice_date_due = ''
            self.from_shipment_charge = ''
            self.invoice_id = False
        return result

    @api.onchange('currency_id')
    def _onchange_currency(self):
        res = super(AccountMove, self)._onchange_currency()
        invoice_data = self.invoice_line_ids
        if self.currency_id and self.currency_id != self._origin.currency_id:
            if self.journal_id.currency_id != invoice_data.shipment_charge_currency_id:
                self.invoice_line_ids = [(5, 0, 0)]
                self.line_ids = [(5, 0, 0)]
                self.from_shipment_charge = ''

        return res

    def action_open_invoices(self):
        self.ensure_one()

        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.reversed_entry_id.id,
        }

    def action_open_credit_notes(self):
        self.ensure_one()

        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'domain': [('reversed_entry_id', '=', self.id)],
            'view_mode': 'tree,form',
            'res_model': self._name,
            'views': [(self.env.ref('account.view_invoice_tree').id, 'tree'), (False, 'form')],
        }

    def action_open_bills(self):
        self.ensure_one()

        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.reversed_entry_id.id,
        }

    def action_open_debit_notes(self):
        self.ensure_one()

        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'domain': [('reversed_entry_id', '=', self.id)],
            'view_mode': 'tree,form',
            'res_model': self._name,
            'views': [(self.env.ref('account.view_in_invoice_refund_tree').id, 'tree'), (False, 'form')],
        }

    def action_post(self):
        move_type_mapping = {
            'out_invoice': _('Invoice'),
            'out_refund': _('Credit Note'),
            'in_invoice': _('Bill'),
            'in_refund': _('Debit Note'),
            'out_receipt': _('Sales Receipt'),
            'in_receipt': _('Purchase Receipt'),
        }
        for move in self:
            if (not move.invoice_line_ids or not move.amount_total) and move.move_type in move_type_mapping:
                raise ValidationError(_('%s with a zero amount cannot be confirmed.') % (move_type_mapping[move.move_type]))

        for move in self.filtered(lambda x: x.move_type == 'out_invoice' or x.move_type == 'in_invoice'):
            if move.add_charges_from == 'master':
                charges = move.line_ids.mapped('master_shipment_charge_cost_id')
            else:
                charges = move.line_ids.mapped('house_shipment_charge_revenue_id') or move.line_ids.mapped('house_shipment_charge_cost_id')
            for charge in charges:
                move_line_ids = charge.move_line_ids.filtered(lambda x: x.shipment_charge_currency_id == move.currency_id and x.parent_state != 'cancel')
                if move_line_ids and sum(move_line_ids.mapped('price_subtotal')) > charge.total_currency_amount:
                    raise ValidationError(_(f'Can not generate {move_type_mapping[move.move_type]} grater then the charge amount'))

        # Validating refund line for amount not greater than what is already raised
        for move in self.filtered(lambda x: x.reversed_entry_id and x.move_type in ['out_refund', 'in_refund']):

            # Getting all product from reversed entry
            reversed_entry = move.reversed_entry_id
            reversed_lines = reversed_entry.mapped('invoice_line_ids')
            for reversed_product in reversed_lines.mapped('product_id'):
                original_product_total = sum(reversed_lines.filtered_domain([('product_id', '=', reversed_product.id)]).mapped('price_subtotal'))
                refund_product_total = sum(move.invoice_line_ids.filtered_domain([('product_id', '=', reversed_product.id)]).mapped('price_subtotal'))
                if original_product_total < refund_product_total:
                    raise ValidationError(
                        _(f'Can not generate {move_type_mapping[move.move_type]} with greater than the \
{move_type_mapping[move.reversed_entry_id.move_type]} amount for product "{reversed_product.name}"')
                    )
            total = move.amount_total

            if total > move.reversed_entry_id.amount_total:
                raise ValidationError(_(f'Can not generate {move_type_mapping[move.move_type]} with greater than the {move_type_mapping[move.reversed_entry_id.move_type]} total amount'))

        return super().action_post()

    def _create_shipment_revenue_invoice_wizard(self, house_shipment_id, charges):
        self.ensure_one()
        record = self.env['shipment.charge.invoice.wizard'].create({
            'charge_ids': [(6, False, charges.ids)],
            'house_shipment_id': house_shipment_id.id,
            'partner_mode': 'specific',
            'partner_ids': [(6, 0, self.partner_id.ids)],
            'single_currency_billing': True,
            'currency_id': self.currency_id.id,
        })
        record._onchange_field_values()
        record._onchange_currency_id()
        return record

    def _create_shipment_cost_invoice_wizard(self, house_shipment_id, charges):
        self.ensure_one()
        record = self.env['shipment.charge.bill.wizard'].create({
            'charge_ids': [(6, False, charges.ids)],
            'house_shipment_id': house_shipment_id.id,
            'partner_mode': 'specific',
            'partner_ids': [(6, 0, self.partner_id.ids)],
            'single_currency_billing': True,
            'currency_id': self.currency_id.id,
        })
        record._onchange_field_values()
        record._onchange_currency_id()
        record.action_generate_bill_lines()
        return record

    def add_revenues_from_house_shipment(self):
        self.ensure_one()
        invoice_lines = []
        self.clear_house_shipment_from_move_line()
        shipment_charge_invoice_wizard_id = self.env['shipment.charge.invoice.wizard']
        charges_to_invoice = False
        for house_shipment_id in self.charge_house_shipment_ids:
            charges_to_invoice = house_shipment_id.revenue_charge_ids.sudo().filtered(
                lambda charge: charge.status in ('no', 'partial') and charge.company_id.id == self.company_id.id)
            if not charges_to_invoice:
                continue
            shipment_charge_invoice_wizard_id |= self._create_shipment_revenue_invoice_wizard(house_shipment_id, charges_to_invoice)
        if shipment_charge_invoice_wizard_id:
            for wizard_line_id in shipment_charge_invoice_wizard_id.line_ids:
                invoice_lines += wizard_line_id._prepare_invoice_line(self.move_type)
        ref = ', '.join(shipment_charge_invoice_wizard_id.mapped('house_shipment_id.booking_nomination_no'))
        charges_for_currency = charges_to_invoice and charges_to_invoice.filtered(lambda x: x.amount_currency_id == self.currency_id) or False
        amount_conversion_rate = charges_for_currency and charges_for_currency[0].amount_conversion_rate or 0.0
        if not charges_for_currency and charges_to_invoice and self.invoice_date:
            amount_conversion_rate = 1 / (self.currency_id._get_conversion_rate(
                charges_to_invoice[0].currency_id, self.currency_id, self.company_id, self.invoice_date) or 1.0)

        self.write({
            'invoice_line_ids': invoice_lines,
            'ref': ref,
            'booking_reference': ref,
            'from_shipment_charge': True,
            'invoice_origin': ref,
            'currency_exchange_rate':  amount_conversion_rate or self.currency_exchange_rate
        })

    def clear_house_shipment_from_move_line(self):
        for record in self:
            house_line = record.invoice_line_ids.filtered(lambda line: line.house_shipment_id or line.house_shipment_id.id in record.charge_house_shipment_ids.ids)
            if house_line:
                house_line.with_context(check_move_validity=False).unlink()

    def clear_master_shipment_from_move_line(self):
        for record in self:
            master_line = record.invoice_line_ids.filtered(lambda line: line.master_shipment_id or line.master_shipment_id.id in record.charge_master_shipment_ids.ids)
            if master_line:
                master_line.with_context(check_move_validity=False).unlink()

    def add_cost_from_house_shipment(self):
        self.ensure_one()
        invoice_lines = []
        self.clear_house_shipment_from_move_line()
        shipment_charge_bill_wizard_id = self.env['shipment.charge.bill.wizard']
        charges_to_bill = False
        for house_shipment_id in self.charge_house_shipment_ids:
            charges_to_bill = house_shipment_id.cost_charge_ids.filtered(
                lambda line: line.partner_id == self.partner_id and line.status in ('no', 'partial') and line.company_id.id == self.company_id.id)
            if not charges_to_bill:
                continue
            shipment_charge_bill_wizard_id |= self._create_shipment_cost_invoice_wizard(house_shipment_id, charges_to_bill)
        if shipment_charge_bill_wizard_id:
            for wizard_line_id in shipment_charge_bill_wizard_id.line_ids:
                invoice_lines += wizard_line_id._prepare_invoice_line(self.move_type)
        ref = ', '.join(shipment_charge_bill_wizard_id.mapped('house_shipment_id.booking_nomination_no'))
        self.write({
            'invoice_line_ids': invoice_lines,
            'booking_reference': ref,
            'from_shipment_charge': True,
            'invoice_origin': ref,
        })

    def _create_master_shipment_cost_invoice_wizard(self, master_shipment_id, charges):
        self.ensure_one()
        record = self.env['master.shipment.charge.bill.wizard'].create({
            'charge_ids': [(6, False, charges.ids)],
            'master_shipment_id': master_shipment_id.id,
            'partner_mode': 'specific',
            'partner_ids': [(6, 0, self.partner_id.ids)],
            'single_currency_billing': True,
            'currency_id': self.currency_id.id,
        })
        record._onchange_field_values()
        record._onchange_currency_id()
        record.action_generate_bill_lines()
        return record

    def add_cost_from_master_shipment(self):
        self.ensure_one()
        invoice_lines = []
        self.clear_master_shipment_from_move_line()
        master_shipment_charge_invoice_wizard_id = self.env['master.shipment.charge.bill.wizard']
        for master_shipment_id in self.charge_master_shipment_ids:
            charges_to_bill = master_shipment_id.cost_charge_ids.filtered(
                lambda charge: charge.partner_id == self.partner_id and not charge.has_bill and charge.status == "adjusted" and charge.company_id.id == self.company_id.id)
            if not charges_to_bill:
                continue
            master_shipment_charge_invoice_wizard_id |= self._create_master_shipment_cost_invoice_wizard(master_shipment_id, charges_to_bill)
        if master_shipment_charge_invoice_wizard_id:
            for wizard_line_id in master_shipment_charge_invoice_wizard_id.line_ids:
                invoice_lines += wizard_line_id._prepare_invoice_line(self.move_type)
        ref = ', '.join(master_shipment_charge_invoice_wizard_id.mapped('master_shipment_id').mapped('house_shipment_ids.booking_nomination_no'))
        self.write({
            'invoice_line_ids': invoice_lines,
            'from_shipment_charge': True,
            'invoice_origin': ref,
            'booking_reference': ref
        })

    def write(self, values):
        # Vendor Tag update
        if values.get('partner_id') and self.move_type in ['in_invoice', 'in_refund']:
            partner = self.env['res.partner'].browse(values.get('partner_id'))
            if partner:
                partner.update_vendor_tag()

        diff_currency_move = False
        if values.get('currency_id'):
            diff_currency_move = self.filtered(lambda move: move.currency_id.id != values.get('currency_id') and move.move_type in ('in_invoice', 'out_invoice'))
        res = super().write(values)
        if diff_currency_move:
            for move in diff_currency_move:
                new_currency_id = values['currency_id']
                move.add_charges_from_house_shipment()
                move.invoice_line_ids.write({'shipment_charge_currency_id': new_currency_id})
        if not self._context.get('skip_line_updates'):
            for move in self.filtered(lambda move: move.move_type in ('in_invoice', 'out_invoice')):
                if move.add_charges_from:
                    if (values.get('charge_house_shipment_ids') or values.get('charge_master_shipment_ids') or values.get('add_charges_from')):
                        move.add_charges_from_house_shipment()
                else:
                    self.clear_house_shipment_from_move_line()
                    self.clear_master_shipment_from_move_line()
        return res

    def add_charges_from_house_shipment(self):
        self.ensure_one()
        if self.move_type == "out_invoice":
            self.add_revenues_from_house_shipment()
        if self.move_type == "in_invoice":
            if self.add_charges_from == 'house':
                self.add_cost_from_house_shipment()
            if self.add_charges_from == 'master':
                self.add_cost_from_master_shipment()

    @api.depends('partner_id', 'company_id', 'currency_id', 'state')
    def _compute_allowed_invoice_bill_moves(self):
        AccountMove_obj = self.env['account.move']
        for rec in self:
            move_type = 'out_invoice' if rec.move_type == 'out_refund' else 'in_invoice'
            domain = [('partner_id', '=', rec.partner_id.id), ('state', '=', 'posted'), ('reversal_move_id', '=', False),
                      ('company_id', '=', rec.company_id.id), ('currency_id', '=', rec.currency_id.id), ('move_type', '=', move_type)]
            rec.allowed_invoice_bill_moves = [(6, 0, AccountMove_obj.search(domain).ids)]

    def action_fetch_invoice(self):
        self.ensure_one()

        if not self.invoice_id:
            raise ValidationError(_("Please select invoice to adjust against credit note."))
        if self.invoice_id.state != "posted":
            raise ValidationError(_('You can only reverse posted moves.'))
        if self.reversed_entry_id:
            raise ValidationError(_('Credit Note already reversed.'))

        default_values = self.env['account.move.reversal']._prepare_default_reversal(self.invoice_id)
        move_vals_list = self.invoice_id.with_context(move_reverse_cancel=False)._reverse_move_vals(default_values, cancel=False)
        line_ids = move_vals_list['line_ids']
        self.write({'line_ids': line_ids, 'ref': default_values.get('ref'), 'reversed_entry_id': self.invoice_id.id})

    def action_adjust_invoice_against_credit(self):
        self.ensure_one()
        move_type = 'out_invoice' if self.move_type == 'out_refund' else 'in_invoice'

        line_lst = []

        move_ids = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id), ('move_type', '=', move_type),
            ('company_id', '=', self.company_id.id), ('currency_id', '=', self.currency_id.id),
            ('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial'))])
        for move in move_ids:

            line_lst.append((0, 0, {'move_id': move.id,
                                    'amount_total_signed': abs(move.amount_total_in_currency_signed),
                                    'actual_amount_due': abs(move.amount_total_in_currency_signed),
                                    'amount_residual_signed': abs(move.amount_total_in_currency_signed)
                                    }))

        return {
            'name': _("Adjust Invoice"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'adjust.invoice.wizard',
            'target': 'new',
            'context': {
                'default_company_id': self.company_id.id,
                'default_currency_id': self.currency_id.id,
                'default_line_ids': line_lst,
                'default_balance_amount': self.amount_residual,
                'default_credit_move_id': self.id
                }
        }

    def _get_invoice_move_line_domain(self):
        self.ensure_one()
        pay_term_lines = self.line_ids \
            .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        return [
            ('move_id', '=', self.id),
            ('account_id', 'in', pay_term_lines.account_id.ids),
            ('parent_state', '=', 'posted'),
            ('partner_id', '=', self.partner_id.id),
            ('reconciled', '=', False),
            '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0)
            ]

    def add_charges_from_master_shipment(self):
        self.ensure_one()
        if self.move_type == "in_invoice":
            self.add_cost_from_master_shipment()

    def _parse_line_data(self, line, sequence):
        return {
            "product_id": line.product_id and line.product_id.name or '',
            "name": line.name,
            "quantity": line.quantity,
            "currency_id": line.currency_id and line.currency_id.name or '',
            "currency_exchange_rate": "",
            "price_unit": line.price_unit or '',
            "FCY_Amt": '% 0.2f' % (line.price_unit * line.quantity * 1),
            "vat": '% 0.2f' % line.l10n_ae_vat_amount,
            "Amount": '% 0.2f' % (line.price_subtotal),
            "house_shipment_id": line.house_shipment_id and line.house_shipment_id.name or '',
            "service_job_id": '',
            "unit": '',
            "display_type": "" if not line.display_type else line.display_type,
            "sequence": sequence,
            "tax_ids": ', '.join(line.mapped('tax_ids').filtered(lambda tax: tax.description).mapped('description'))
        }

    def _create_section_total(self, total_amount, sequence):
        return {
            "product_id": '',
            "name": 'Total',
            "quantity": 0,
            "currency_id": '',
            "currency_exchange_rate": "",
            "price_unit": '',
            "FCY_Amt": '0.0',
            "vat": '',
            "Amount": '% 0.2f' % (total_amount),
            "house_shipment_id": '',
            "service_job_id": '',
            "unit": '',
            "display_type": 'line_section_total',
            "sequence": sequence,
            "tax_ids": ''
        }

    def _process_invoice_line(self, invoice_lines):
        lines = False
        if len(invoice_lines.mapped('sequence')) > 1:
            lines = invoice_lines.sorted(key=lambda line: line.sequence)
        else:
            lines = invoice_lines.sorted(key=lambda line: line.id)
        count = len(lines)
        next_line = False
        vals = []
        seq = 0
        i = 1
        total_amount = 0
        line_section = 0
        for line in lines:
            if not seq:
                seq = line.sequence
            if next_line and line.display_type == 'line_section':
                line_section += 1
                vals.append(self._create_section_total(total_amount, seq))
                seq += 1
                total_amount = 0
            vals.append(self._parse_line_data(line, seq))
            seq += 1
            total_amount += line.price_subtotal
            next_line = True
            if i >= count and line_section >= 1:
                vals.append(self._create_section_total(total_amount, seq))
                seq += 1
            i += 1
        return vals

    def get_invoice_line_for_document(self, group_by=[]):
        house_data_list = []
        if self.add_charges_from and group_by:
            self.invoice_line_ids and self.invoice_line_ids._compute_pre_move_line()
            for house in self.invoice_line_ids.mapped(group_by[0]):
                invoice_line_ids = self.env['account.move.line'].search(
                    [('id', 'in', self.invoice_line_ids.ids), (group_by[0], '=', house.id)])
                all_invoice_line_ids = invoice_line_ids
                all_invoice_line_ids += invoice_line_ids.mapped('account_line_doc_ids')
                if all_invoice_line_ids:
                    amount_total = sum(all_invoice_line_ids.mapped('price_subtotal'))
                    vat_total = sum(all_invoice_line_ids.mapped('l10n_ae_vat_amount'))
                    house_data_list.append({
                        'id': house.id,
                        'name': house.name,
                        'total_amount': '% 0.2f' % (amount_total),
                        'total_amount_in_words': '{} Only'.format(self.currency_id.amount_to_text(amount_total)),
                        'total_vat': '% 0.2f' % (vat_total),
                        'lines': self._process_invoice_line(all_invoice_line_ids)
                    })
        else:
            amount_total = sum(self.invoice_line_ids.mapped('price_subtotal'))
            vat_total = sum(self.invoice_line_ids.mapped('l10n_ae_vat_amount'))
            house_data_list.append({
                'id': '',
                'name': '',
                'total_amount': '% 0.2f' % (amount_total),
                'total_amount_in_words': '{} Only'.format(self.currency_id.amount_to_text(amount_total)),
                'total_vat': '% 0.2f' % (vat_total),
                'lines': self._process_invoice_line(self.invoice_line_ids)
            })

        return house_data_list

    def button_cancel(self):
        res = super().button_cancel()
        for move in self:
            if move.add_charges_from and move.move_type in ['out_invoice', 'in_invoice']:
                refund_move_ids = move.search([('reversed_entry_id', '=', move.id)])
                if refund_move_ids and any(refund_move.state != 'cancel' for refund_move in refund_move_ids):
                    raise UserError(_(f"Need to cancel {dict(move._fields['move_type'].selection).get(refund_move_ids[0].move_type)}."))
        return res
