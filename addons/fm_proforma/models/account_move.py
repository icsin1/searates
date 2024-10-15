# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    pro_forma_invoice_id = fields.Many2one('pro.forma.invoice', copy=False)

    def unlink(self):
        for rec in self:
            if rec.pro_forma_invoice_id:
                rec.pro_forma_invoice_id.write({'state': 'to_approve'})
        return super(AccountMove, self).unlink()

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        for move in self:
            if move.pro_forma_invoice_id and all(invoice.state == 'cancel' for invoice in move.pro_forma_invoice_id.move_ids):
                move.pro_forma_invoice_id.action_cancel_pro_forma()
        return res

    def button_draft(self):
        super(AccountMove, self).button_draft()
        for move in self:
            if move.pro_forma_invoice_id:
                move.pro_forma_invoice_id.state = 'invoiced'
