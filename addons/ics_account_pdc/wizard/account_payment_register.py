# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.depends('payment_method_line_id')
    def _compute_show_cheque_information(self):
        for wizard in self:
            wizard.show_cheque_information = wizard.payment_method_line_id.code == 'pdc'

    cheque_no = fields.Char("Cheque Number")
    cheque_date = fields.Date()
    cheque_ref = fields.Char("Cheque Reference")
    show_cheque_information = fields.Boolean(compute="_compute_show_cheque_information",
                                             help="Technical field used to know whether the cheque related fields "
                                                  "needs to be displayed or not in the payments form views")

    def _create_payment_vals_from_wizard(self):
        res = super()._create_payment_vals_from_wizard()
        if self.show_cheque_information:
            res.update({
                'cheque_no': self.cheque_no,
                'cheque_date': self.cheque_date,
                'cheque_ref': self.cheque_ref,
            })
        return res
