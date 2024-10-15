# -*- coding: utf-8 -*-
from odoo import models


class TariffServiceLineWizard(models.TransientModel):
    _inherit = 'tariff.service.line.wizard'

    def _get_sell_charge_vals(self):
        res = super()._get_sell_charge_vals()
        wiz_rec = self.tariff_service_wiz_id
        if wiz_rec.shipment_quote_id and wiz_rec.multi_carrier_quote:
            res.update({'carrier_id': wiz_rec.carrier_id.id, 'incoterm_id': wiz_rec.incoterm_id.id})
        return res

    def _get_buy_charge_vals(self):
        res = super()._get_buy_charge_vals()
        wiz_rec = self.tariff_service_wiz_id
        if wiz_rec.shipment_quote_id and wiz_rec.multi_carrier_quote:
            res.update({'carrier_id': wiz_rec.carrier_id.id, 'incoterm_id': wiz_rec.incoterm_id.id})
        return res
