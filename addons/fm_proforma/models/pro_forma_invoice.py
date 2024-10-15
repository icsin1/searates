# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError

READONLY_STAGE = {'to_approve': [('readonly', False)]}


class ProFormaInvoice(models.Model):
    _name = 'pro.forma.invoice'
    _description = "Pro Forma Invoice"
    _order = 'create_date DESC'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin', 'image.mixin']
    _check_company_auto = True

    name = fields.Char(required=True, default='New Pro-Forma Invoice')
    user_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user, states=READONLY_STAGE, readonly=True)
    house_shipment_id = fields.Many2one('freight.house.shipment', copy=False, readonly=True)
    charge_house_shipment_ids = fields.Many2many('freight.house.shipment', 'house_proforma_invoice_rel', string=" Charge House Shipment")  # in proforma invoice to link multiple hs

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,
                                 required=True, states=READONLY_STAGE, readonly=True)
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True,
                                          related='company_id.currency_id', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id,
                                  required=True, states=READONLY_STAGE, readonly=True)
    pro_forma_invoice_line_ids = fields.One2many('pro.forma.invoice.line', 'pro_forma_invoice_id',
                                                 string='Pro-forma Invoice Lines', states=READONLY_STAGE, readonly=True)
    state = fields.Selection(
        [('to_approve', 'To Approve'),
         ('sent', 'Sent'),
         ('approved', 'Approved'),
         ('invoiced', 'Invoiced'),
         ('cancel', 'Cancel')],
        default='to_approve', copy=False, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Debtor', states=READONLY_STAGE, readonly=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, compute='_cal_pro_forma_invoice_amount')
    amount_tax = fields.Monetary(string='Taxes', store=True, compute='_cal_pro_forma_invoice_amount')
    amount_total = fields.Monetary(string='Total', store=True, compute='_cal_pro_forma_invoice_amount')
    reject_reason = fields.Text(copy=False, states=READONLY_STAGE, readonly=True)
    signed_by = fields.Char('Signed By', help='Name of the person that signed the Pro-Forma Invoice.', copy=False)
    signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
    image_1920 = fields.Image("Signature", max_width=1920, max_height=1920, copy=False)
    invoice_cash_rounding_id = fields.Many2one('account.cash.rounding', string='Cash Rounding Method')
    move_ids = fields.One2many('account.move', 'pro_forma_invoice_id', string='Invoices', copy=False)
    move_count = fields.Integer(compute='_compute_moves_count', store=True)
    show_shipment_charge_button = fields.Boolean(compute='_compute_show_shipment_charge_button', store=True)

    def unlink(self):
        for rec in self:
            if rec.state not in ['to_approve']:
                raise UserError(_('You cannot delete proforma invoice which is in "%s" state.') % (rec.state,))
        return super(ProFormaInvoice, self).unlink()

    def action_create_invoice(self):
        self.ensure_one()
        if not self.house_shipment_id:
            return
        move_type = 'out_invoice'
        AccountMove = self.env['account.move'].with_context(default_move_type=move_type)
        move_id = AccountMove.create(self._prepare_invoice(move_type))
        move_id.with_context(skip_reset_line=True)._onchange_partner_id()
        self.write({'state': 'invoiced'})
        return self.action_view_invoice(move_id)

    def action_view_invoice(self, invoice):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['context'] = {'create': 0}
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        action['views'] = form_view + [(state, view) for state, view in action.get('views', []) if view != 'form']
        action['res_id'] = invoice.id
        return action

    @api.depends('pro_forma_invoice_line_ids', 'pro_forma_invoice_line_ids.price_subtotal')
    def _cal_pro_forma_invoice_amount(self):
        for rec in self:
            amount_untaxed = amount_tax = 0.0
            for line in rec.pro_forma_invoice_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            rec.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    def action_send_by_email(self):
        self.ensure_one()
        template_id = self._find_mail_template()
        ctx = {
            'default_model': self._name,
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def action_cancel_pro_forma(self):
        self.ensure_one()
        self.state = 'cancel'

    def action_approve_pro_forma(self):
        self.ensure_one()
        self.state = 'approved'

    def preview_pro_forma_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': self.get_portal_url(),
        }

    def action_approve_all_proforma(self):
        for rec in self.filtered(lambda p: p.state in ['to_approve']):
            rec.action_approve_pro_forma()

    def get_access_action(self, access_uid=None):
        self.ensure_one()
        user = access_uid and self.env['res.users'].sudo().browse(access_uid) or self.env.user
        if not user.share:
            return super(ProFormaInvoice, self).get_access_action(access_uid)
        return {
            'type': 'ir.actions.act_url',
            'url': self.get_portal_url(),
            'target': 'self',
            'res_id': self.id,
        }

    def _compute_access_url(self):
        super(ProFormaInvoice, self)._compute_access_url()
        for rec in self:
            rec.access_url = '/my/pro_forma_invoice/%s' % (rec.id)

    def _get_portal_return_action(self):
        self.ensure_one()
        return self.env.ref('fm_proforma.pro_forma_invoice_action')

    def _find_mail_template(self):
        self.ensure_one()
        template_id = self.env['ir.model.data']._xmlid_to_res_id('fm_proforma.pro_forma_invoice_email_template', raise_if_not_found=False)
        if self.state == 'approved':
            template_id = self.env['ir.model.data']._xmlid_to_res_id('fm_proforma.pro_forma_invoice_confirmation_email_template', raise_if_not_found=False)
        if self.state == 'cancel':
            template_id = self.env['ir.model.data']._xmlid_to_res_id('fm_proforma.pro_forma_invoice_reject_email_template', raise_if_not_found=False)
        return template_id

    def send_email_from_portal_action(self):
        if self.env.su:
            self = self.with_user(SUPERUSER_ID)
        template_id = self._find_mail_template()
        if template_id:
            self.with_context(force_send=True).message_post_with_template(
                template_id, composition_mode='comment', email_layout_xmlid="mail.mail_notification_paynow"
            )

    def _send_pro_forma_reject_mail(self):
        self.ensure_one()
        self.send_email_from_portal_action()

    def _send_pro_forma_confirmation_mail(self):
        self.ensure_one()
        self.send_email_from_portal_action()

    def _prepare_invoice(self, move_type):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_move_type=move_type)
        invoice_ref = '{} - {}'.format(self.name, self.house_shipment_id.booking_nomination_no)
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
            'invoice_incoterm_id': self.house_shipment_id.inco_term_id.id,
            'invoice_line_ids': self._prepare_invoice_line(),
            'invoice_date': fields.Date.context_today(self),
            'from_shipment_charge': True,
            'pro_forma_invoice_id': self.id,
            'add_charges_from': 'house',
            'charge_house_shipment_ids': [(6, 0, self.charge_house_shipment_ids.ids or self.house_shipment_id.ids)],   # from pro forma multiple hs has to be linked in Invoice
            'invoice_cash_rounding_id': self.invoice_cash_rounding_id.id if self.invoice_cash_rounding_id else False,
        }

    def _prepare_invoice_line(self):
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
                'house_shipment_charge_revenue_id': pro_forma_line.house_shipment_charge_revenue_id.id,
                'account_id': pro_forma_line.house_shipment_charge_revenue_id.property_account_id.id,
                'currency_exchange_rate': pro_forma_line.currency_exchange_rate,
                'shipment_charge_currency_id': pro_forma_line.shipment_charge_currency_id.id,
                'charge_rate_per_unit': pro_forma_line.charge_rate_per_unit
            }))
        return invoice_lines

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s' % self.name.replace('/', '_')

    def action_reset_to_draft(self):
        self.ensure_one()
        self.state = 'to_approve'

    @api.onchange('invoice_cash_rounding_id')
    def _onchange_recompute_dynamic_lines(self):
        self._recompute_cash_rounding_lines()

    def _recompute_cash_rounding_lines(self):
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _compute_cash_rounding(self, total_amount_currency):
            difference = self.invoice_cash_rounding_id.compute_difference(self.currency_id, total_amount_currency)
            if self.currency_id == self.company_id.currency_id:
                diff_amount_currency = diff_balance = difference
            else:
                diff_amount_currency = difference
                diff_balance = self.currency_id._convert(diff_amount_currency, self.company_id.currency_id, self.company_id, self.house_shipment_id.shipment_date)
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

    def add_charges_from_house_shipment(self):
        self.ensure_one()
        pro_forma_invoice_lines = []
        self.remove_pro_forma_charge_lines()
        shipment_charge_invoice_wizard_ids = self.env['shipment.charge.pro.forma.invoice.wizard']
        to_pro_forma_invoice = False
        for house_shipment_id in self.charge_house_shipment_ids:
            to_pro_forma_invoice = house_shipment_id.revenue_charge_ids.filtered(lambda charge: charge.status in ['no', 'pro_forma_cancel'])
            if not to_pro_forma_invoice:
                continue
            shipment_charge_invoice_wizard_ids |= self._create_shipment_revenue_invoice_wizard(house_shipment_id, to_pro_forma_invoice)

        for wizard_line_id in shipment_charge_invoice_wizard_ids.line_ids:
            pro_forma_invoice_lines += wizard_line_id._prepare_pro_forma_invoice_line()

        self.write({'pro_forma_invoice_line_ids': pro_forma_invoice_lines})
        self._onchange_recompute_dynamic_lines()

    def remove_pro_forma_charge_lines(self):
        self.ensure_one()
        self.pro_forma_invoice_line_ids.unlink()

    def _create_shipment_revenue_invoice_wizard(self, house_shipment_id, charges):
        self.ensure_one()
        record = self.env['shipment.charge.pro.forma.invoice.wizard'].create({
            'charge_ids': [(6, False, charges.ids)],
            'house_shipment_id': house_shipment_id.id,
            'partner_mode': 'specific',
            'partner_ids': [(6, 0, self.partner_id.ids)],
            'single_currency_billing': True,
            'currency_id': self.currency_id.id,
            'invoice_cash_rounding_id': self.invoice_cash_rounding_id.id
        })
        record._onchange_field_values()
        record._onchange_currency_id()
        return record

    @api.depends('move_ids', 'move_ids.state')
    def _compute_moves_count(self):
        for rec in self:
            rec.move_count = len(rec.move_ids)

    def action_open_moves(self):
        self.ensure_one()
        moves = self.move_ids
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['context'] = {'default_pro_forma_invoice_id': self.id, 'default_move_type': 'out_invoice', 'create': 0}
        if len(moves) > 1:
            action['domain'] = [('id', 'in', moves.ids)]
            return action
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        action['views'] = form_view + [(state, view) for state, view in action.get('views', []) if view != 'form']
        action['res_id'] = moves.id
        return action

    @api.depends('charge_house_shipment_ids', 'state')
    def _compute_show_shipment_charge_button(self):
        for rec in self:
            rec.show_shipment_charge_button = rec.charge_house_shipment_ids and rec.state == 'to_approve'


class ProFormaInvoiceLine(models.Model):
    _name = 'pro.forma.invoice.line'
    _description = "Pro Forma Invoice Line"

    pro_forma_invoice_id = fields.Many2one('pro.forma.invoice', copy=False, ondelete='cascade')
    house_shipment_charge_revenue_id = fields.Many2one('house.shipment.charge.revenue', copy=False)
    product_id = fields.Many2one('product.product', string='Charge Type',
                                 domain=lambda self: [('categ_id', '=', self.env.ref('freight_base.shipment_charge_category').id)])
    service_name = fields.Char(string='Charge Desc.', required=True)
    company_id = fields.Many2one(related='pro_forma_invoice_id.company_id', store=True, readonly=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency')
    product_uom_id = fields.Many2one('uom.uom', string='UoM')
    quantity = fields.Float(string='Quantity', default=1, required=True)
    sell_currency_id = fields.Many2one('res.currency', string='Sell Currency')
    price_unit = fields.Monetary(string='Unit Price', currency_field='sell_currency_id')
    tax_ids = fields.Many2many('account.tax', 'pro_forma_invoice_tax_default_rel', string='Taxes', copy=False)
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,
                                     currency_field='sell_currency_id', compute='_compute_amount')
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', store=True)
    shipment_charge_currency_id = fields.Many2one('res.currency', copy=False, string='Currency')
    currency_exchange_rate = fields.Float('Ex.Rate', copy=False, digits='Currency Exchange Rate')
    charge_rate_per_unit = fields.Float('Amount/Qty', copy=False, digits='Product Price')
    is_rounding_line = fields.Boolean(help="Technical field used to retrieve the cash rounding line.")
    account_id = fields.Many2one('account.account', string='Account')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            rec.service_name = rec.product_id.name
            rec.product_uom_id = rec.product_id.uom_id.id

    @api.depends('quantity', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        for line in self:
            taxes = line.tax_ids.compute_all(line.price_unit, line.pro_forma_invoice_id.currency_id,
                                             line.quantity, product=line.product_id,
                                             partner=line.pro_forma_invoice_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_subtotal': taxes['total_excluded'],
            })
