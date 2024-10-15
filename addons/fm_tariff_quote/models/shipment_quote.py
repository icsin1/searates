# -*- coding: utf-8 -*-
from odoo import models


class ShipmentQuote(models.Model):
    _inherit = "shipment.quote"

    def prepare_tariff_service_wizard_vals(self):
        self.ensure_one()
        return {
            'shipment_quote_id': self.id,
            'shipment_type_id': self.shipment_type_id.id,
            'transport_mode_id': self.transport_mode_id.id,
            'cargo_type_id': self.cargo_type_id.id,
            'tariff_type': self._context.get('tariff_type'),
            'origin_id': self.origin_un_location_id.id,
            'origin_port_id': self.port_of_loading_id.id,
            'destination_id': self.destination_un_location_id.id,
            'destination_port_id': self.port_of_discharge_id.id,
            'company_id': self.company_id.id,
            'customer_id': self.client_id.id if self._context.get('tariff_type') == 'sell_tariff' else False,
            'vendor_ids': [],
            'sell_charge_master': True if self._context.get('tariff_type', 'charge_master') in ['sell_tariff', 'charge_master'] else False,
            'buy_charge_master': True if self._context.get('tariff_type', 'charge_master') in ['buy_tariff', 'charge_master'] else False,
            'tariff_for': self.quote_for,
        }

    def action_tariff_services_wizard(self):
        self.ensure_one()
        action = self.env.ref('fm_tariff.tariff_service_wizard_wizard_action').sudo().read()[0]
        wiz_tariff_service = self.env['tariff.service.wizard'].create(self.prepare_tariff_service_wizard_vals())
        wiz_tariff_service.action_fetch_tariff()
        ctx = self._context.copy()
        action['name'] = '{}: Fetch from {}'.format(self.name, str(ctx.get('tariff_type')).replace('_', ' ').title())
        action['domain'] = [('id', '=', wiz_tariff_service.id)]
        action['res_id'] = wiz_tariff_service.id
        return action

    def action_remove_all_services(self):
        self.ensure_one()
        self.quotation_line_ids.unlink()
