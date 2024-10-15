# -*- coding: utf-8 -*-
from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        res['compute_tds'] = move.compute_tds
        return res
