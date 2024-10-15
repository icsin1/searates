# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TariffMixin(models.AbstractModel):
    _inherit = 'tariff.mixin'

    incoterm_id = fields.Many2one('account.incoterms', string='Incoterms', copy=False)

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        super()._onchange_transport_mode_id()
        self.incoterm_id = False
