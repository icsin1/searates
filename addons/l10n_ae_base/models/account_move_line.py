# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_ae_vat_amount = fields.Monetary(string='Tax Amount')
