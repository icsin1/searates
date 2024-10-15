# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_in_gstin_partner_id = fields.Many2one('res.partner', tracking=True)
