# -*- coding: utf-8 -*-

import json
import base64

from odoo import models, fields, api, _


EINV_STATUS_HELP = {
    'draft': _('Requested'),
    'in_process': _('Processing'),
    'failed': _('Failed'),
    'done': _('Done'),
}


class AccountMove(models.Model):
    _inherit = "account.move"

    einvoice_request_uuid = fields.Char(copy=False)
    einvoice_request_status = fields.Char(copy=False)
    einvoice_request_status_help = fields.Char(copy=False)
    einvoice_request_fail_reason = fields.Char(copy=False)
    einvoice_request_status_computed = fields.Char(compute='_compute_einvoice_request_status_computed', store=True)
    einvoice_cancel_reason = fields.Selection(selection=[
        ('1', 'Duplicate'),
        ('2', 'Data Entry Mistake'),
        ('3', 'Order Cancelled'),
        ('4', 'Others'),
        ], string='Cancel reason', default='1', tracking=True)
    einvoice_cancel_remarks = fields.Text(string='Cancel Remarks', copy=False, tracking=True)
    einvoice_show_cancel = fields.Boolean(compute='_compute_einvoice_show_cancel', string='SR E-invoice is sent?')
    einvoice_irn = fields.Char('IRN', copy=False)

    def _get_document_type(self):
        self.ensure_one()
        return 'credit_note' if self.move_type == 'out_refund' else 'invoice'

    def _get_is_overseas(self):
        self.ensure_one()
        return bool(self.partner_id.country_id.code != self.company_id.country_id.code)

    def _get_supply_type(self):
        self.ensure_one()
        return 'B2B'

    def _get_is_tax_reverse_charge(self):
        self.ensure_one()
        return False

    def _get_export_details(self):
        self.ensure_one()
        return {
            'shipping_bill_number': None,
            'shipping_bill_date': None,
            'shipping_port_code': None
        }

    @api.depends('edi_document_ids', 'edi_document_ids.state')
    def _compute_einvoice_show_cancel(self):
        for invoice in self:
            invoice.einvoice_show_cancel = bool(invoice.edi_document_ids.filtered(
                lambda i: i.edi_format_id.code == "edi_sr_env"
            ))

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        # Trigger process EDI
        edi_moves = posted.filtered(lambda posted_move: posted_move.edi_web_services_to_process)
        if edi_moves:
            edi_moves.button_process_edi_web_services()
        return posted

    def button_cancel_posted_moves(self):
        '''Customization: Call this method with-context "action_open_cancel_reason:True" to open cancellation reason wizard'''
        if self._context.get('action_open_cancel_reason'):
            form_view_id = self.env.ref('ics_account_edi.account_move_cancel_edi_view_form').sudo().id
            return {
                'name': "%s: EDI Cancellation" % (self[0].name),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [(form_view_id, 'form')],
                'res_model': self._name,
                'res_id': self[0].id,
                'target': 'new',
                'context': {'form_view_initial_mode': 'edit', **self._context},
            }
        self.write({'einvoice_request_status': ''})
        self.button_process_check_status()
        res = super().button_cancel_posted_moves()
        # Trigger process EDI
        self.button_process_edi_web_services()
        return res

    def _get_edi_response_json(self):
        self.ensure_one()
        edi_document = self.edi_document_ids.filtered(lambda i: i.edi_format_id.code == "edi_sr_env" and i.state in ("sent", "to_cancel"))
        if edi_document:
            return json.loads(edi_document.attachment_id.raw.decode("utf-8"))
        else:
            return {}

    def _prepare_tax_grouping_key(self, tax_values):
        tax_values['line_code'] = tax_values.get('tax_id').name
        return tax_values

    def _prepare_edi_tax_details(self, filter_to_apply=None, filter_invl_to_apply=None, grouping_key_generator=None, compute_mode='tax_details'):
        def _ics_grouping_key_generator(tax_values):
            return self._prepare_tax_grouping_key(tax_values)

        _grouping_key_generator = grouping_key_generator or _ics_grouping_key_generator
        return super()._prepare_edi_tax_details(filter_to_apply=filter_to_apply, filter_invl_to_apply=filter_invl_to_apply, grouping_key_generator=_grouping_key_generator, compute_mode=compute_mode)

    def button_process_check_status(self):
        docs = self.edi_document_ids
        docs._process_documents_status_check_web_services()

    def _cron_process_check_status(self):
        account_moves = self.search([('state', '!=', 'draft'), ('edi_state', 'not in', ['to_sent', False]), ('einvoice_request_status', '!=', 'done')])
        for account_move in account_moves:
            account_move.button_process_check_status()

    def action_force_retry_edi(self):
        self.action_retry_edi_documents_error()

    @api.depends('einvoice_request_status')
    def _compute_einvoice_request_status_computed(self):
        for rec in self:
            rec.einvoice_request_status_computed = EINV_STATUS_HELP.get(rec.einvoice_request_status, rec.einvoice_request_status)

    def _get_edi_invoice_report(self):
        self.ensure_one()
        report = self.env.ref(self._get_default_account_report())
        document = report._render([self.id])
        return base64.b64encode(document[0]).decode('utf-8')

    def _get_edi_attachments(self):
        self.ensure_one()
        attachments = [{
            'attachment_type': 'invoice',
            'attachment_mimetype': 'application/pdf',
            'attachment_data': self._get_edi_invoice_report(),
            'attachment_filename': "inv_{}.pdf".format(self.id)
        }]
        return attachments

    def _get_default_account_report(self):
        return 'account.account_invoices'

    def _retry_edi_documents_error_hook(self):
        self.write({'einvoice_request_status': False, 'edi_web_services_to_process': False})
        self.edi_document_ids.write({'state': 'to_send'})
        return super()._retry_edi_documents_error_hook()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    amount_currency_untaxed = fields.Monetary(string='Amount Untaxed', currency_field='currency_id', compute='_compute_amount_currency_untaxed', store=True)

    def _get_product_unit(self):
        self.ensure_one()
        return self.product_uom_id.name

    @api.depends('price_total', 'price_subtotal')
    def _compute_amount_currency_untaxed(self):
        for move_line in self:
            vat_amount = move_line.price_total - move_line.price_subtotal
            move_line.amount_currency_untaxed = move_line.price_total - vat_amount

    def _get_edi_product_identifier(self):
        self.ensure_one()
        return self.product_id and self.product_id.default_code or str(self.id)

    def _get_edi_taxes(self):
        self.ensure_one()
        taxes = []
        for tax_line in self.tax_ids:
            for tax in tax_line if tax_line.amount_type != 'group' else tax_line.children_tax_ids:
                tax_code = self._get_edi_tax_code(tax, self)
                tax_amount = tax._compute_amount(self.price_subtotal, self.price_unit, self.quantity, product=self.product_id, partner=self.partner_id)
                taxes.append({
                    'tax_label': tax.description,
                    'tax_code': tax_code,
                    'tax_computation_mode': tax.amount_type,
                    'tax_percentage': tax.amount,
                    'tax_amount': tax_amount,
                    'tax_country_code': tax.country_id.code.upper(),
                    'tax_taxable_amount': self.price_subtotal
                })
        return taxes

    def _get_edi_tax_code(self, tax, tax_line):
        self.ensure_one()
        return tax.tax_group_id and tax.tax_group_id.name or str(tax.id)
