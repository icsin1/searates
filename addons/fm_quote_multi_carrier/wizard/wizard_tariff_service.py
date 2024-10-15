# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TariffServiceWizard(models.TransientModel):
    _inherit = 'tariff.service.wizard'

    multi_carrier_quote = fields.Boolean(related='shipment_quote_id.multi_carrier_quote', store=True)
    carrier_id = fields.Many2one('freight.carrier', string='Shipping Line')
    incoterm_id = fields.Many2one('account.incoterms', string='Incoterms')
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id_field(self):
        self.update({'incoterm_id': False, 'carrier_id': False})

    @api.onchange('carrier_id', 'incoterm_id')
    def _onchange_multi_carrier_quote(self):
        self.action_fetch_tariff()

    def get_buy_tariff_domain(self):
        domain = super(TariffServiceWizard, self).get_buy_tariff_domain()
        if not self.multi_carrier_quote:
            return domain
        if self.carrier_id:
            domain += [('buy_tariff_id.carrier_id', '=', self.carrier_id.id)]
        if self.incoterm_id:
            domain += [('buy_tariff_id.incoterm_id', '=', self.incoterm_id.id)]
        return domain

    def get_sell_tariff_domain(self):
        domain = super(TariffServiceWizard, self).get_sell_tariff_domain()
        if not self.multi_carrier_quote:
            return domain
        if self.carrier_id:
            domain += [('sell_tariff_id.carrier_id', '=', self.carrier_id.id)]
        if self.incoterm_id:
            domain += [('sell_tariff_id.incoterm_id', '=', self.incoterm_id.id)]
        return domain
