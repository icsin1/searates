# -*- coding: utf-8 -*-
from odoo import models, fields


class WizardAccountGlobalTDSTax(models.TransientModel):
    _name = 'wizard.account.global.tds.tax'
    _description = "Account Global TDS Tax"

    tds_tax_id = fields.Many2one('account.tax', string='TDS Tax', required=True, domain=lambda self: [('type_tax_use', '=', 'purchase'),
                                                                                                      ('tax_group_id', '=', self.env.ref('l10n_in_tds_tcs.tds_group').id)])
    account_move_id = fields.Many2one('account.move', string="Account Move")

    def action_apply_tds_on_moves(self):
        self.account_move_id.write({'tds_tax_id': self.tds_tax_id.id})
