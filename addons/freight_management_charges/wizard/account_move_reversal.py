# -*- coding: utf-8 -*-
from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        res['from_shipment_charge'] = move.from_shipment_charge
        res['invoice_id'] = move.id
        return res
