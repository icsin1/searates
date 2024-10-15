from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('payment_method_line_id')
    def _compute_show_cheque_information(self):
        for payment in self:
            payment.show_cheque_information = payment.payment_method_line_id.code == 'pdc'

    def _compute_pdc_payment_returned(self):
        for payment in self:
            payment.pdc_payment_returned = payment.pdc_payment_id.state in ['returned', 'bounced']

    cheque_no = fields.Char("Cheque Number", copy=False)
    cheque_date = fields.Date(copy=False)
    cheque_ref = fields.Char("Cheque Reference", copy=False)
    show_cheque_information = fields.Boolean(compute="_compute_show_cheque_information",
                                             help="Technical field used to know whether the cheque related fields "
                                                  "needs to be displayed or not in the payments form views")
    pdc_payment_id = fields.Many2one('pdc.payment', copy=False)
    pdc_payment_returned = fields.Boolean(compute="_compute_pdc_payment_returned")

    def _prepare_pdc_payment_vals(self):
        return {
            'name': self.cheque_no,
            'date': self.cheque_date,
            'currency_id': self.currency_id.id,
            'payment_date': self.date,
            'journal_id': self.journal_id.id,
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'cheque_ref': self.cheque_ref,
        }

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.payment_method_line_id.code == 'pdc':
            pdc_payment_vals = res._prepare_pdc_payment_vals()
            pdc_payment_vals.update({
                'payment_id': res.id
            })
            pdc_payment_id = self.env['pdc.payment'].create(pdc_payment_vals)
            res.pdc_payment_id = pdc_payment_id.id
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get('payment_method_line_id'):
            for payment in self:
                if payment.payment_method_line_id.code == 'pdc':
                    pdc_payment_vals = payment._prepare_pdc_payment_vals()
                    pdc_payment_vals.update({
                        'payment_id': payment.id
                    })
                    pdc_payment_id = self.env['pdc.payment'].create(pdc_payment_vals)
                    payment.pdc_payment_id = pdc_payment_id.id
        return res

    def button_open_pdc_payment(self):
        self.ensure_one()
        return {
            'name': _("PDC Payment"),
            'type': 'ir.actions.act_window',
            'res_model': 'pdc.payment',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.pdc_payment_id.id,
        }

    def _get_valid_liquidity_accounts(self):
        res = super()._get_valid_liquidity_accounts()
        if isinstance(res, tuple):
            res += (self.company_id.pdc_receivable_account_id, self.company_id.pdc_payable_account_id)
        else:
            res |= self.company_id.pdc_receivable_account_id
            res |= self.company_id.pdc_payable_account_id
        return res

    def _compute_outstanding_account_id(self):
        super()._compute_outstanding_account_id()
        for pay in self.filtered(lambda p: p.payment_method_line_id.code == 'pdc'):
            if pay.payment_type == 'inbound':
                pay.outstanding_account_id = pay.company_id.pdc_receivable_account_id
            elif pay.payment_type == 'outbound':
                pay.outstanding_account_id = pay.company_id.pdc_payable_account_id
