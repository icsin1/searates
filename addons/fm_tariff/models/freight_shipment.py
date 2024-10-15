# -*- coding: utf-8 -*-
from odoo import models


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    def action_tariff_services_wizard(self, model):
        self.ensure_one()
        action = self.env.ref('fm_tariff.tariff_service_wizard_wizard_action').sudo().read()[0]
        vendors = self.shipment_partner_ids.filtered(lambda partner: partner.partner_type_id.is_vendor).mapped('partner_id')
        ctx = self._context.copy()
        wiz_tariff_service = self.env['tariff.service.wizard'].create({
            'house_shipment_id': self.id,
            'shipment_type_id': self.shipment_type_id.id,
            'transport_mode_id': self.transport_mode_id.id,
            'cargo_type_id': self.cargo_type_id.id,
            'tariff_type': ctx.get('tariff_type', 'charge_master'),
            'origin_id': self.origin_un_location_id.id,
            'origin_port_id': self.origin_port_un_location_id.id,
            'destination_id': self.destination_un_location_id.id,
            'destination_port_id': self.destination_port_un_location_id.id,
            'company_id': self.company_id.id,
            'customer_id': self.client_id.id if ctx.get('tariff_type') == 'sell_tariff' else False,
            'vendor_ids': vendors and vendors.ids if ctx.get('tariff_type') == 'buy_tariff' else [],
            'sell_charge_master': True if model == 'house.shipment.charge.revenue' else False,
            'buy_charge_master': True if model == 'house.shipment.charge.cost' else False,
            'tariff_for': 'shipment',
        })
        wiz_tariff_service.action_fetch_tariff()
        action['name'] = '{}: Fetch from {}'.format(self.name, str(ctx.get('tariff_type')).replace('_', ' ').title())
        action['domain'] = [('id', '=', wiz_tariff_service.id)]
        action['res_id'] = wiz_tariff_service.id
        return action


class FreightMasterShipment(models.Model):
    _inherit = 'freight.master.shipment'

    def action_tariff_services_wizard(self, model):
        self.ensure_one()
        action = self.env.ref('fm_tariff.tariff_service_wizard_wizard_action').sudo().read()[0]
        ctx = self._context.copy()
        wiz_tariff_service = self.env['tariff.service.wizard'].create({
            'master_shipment_id': self.id,
            'shipment_type_id': self.shipment_type_id.id,
            'transport_mode_id': self.transport_mode_id.id,
            'cargo_type_id': self.cargo_type_id.id,
            'tariff_type': ctx.get('tariff_type', 'charge_master'),
            'origin_id': self.origin_un_location_id.id,
            'origin_port_id': self.origin_port_un_location_id.id,
            'destination_id': self.destination_un_location_id.id,
            'destination_port_id': self.destination_port_un_location_id.id,
            'company_id': self.company_id.id,
            'customer_id': False,
            'vendor_ids': [],
            'sell_charge_master': True if model == 'master.shipment.charge.revenue' else False,
            'buy_charge_master': True if model == 'master.shipment.charge.cost' else False,
            'tariff_for': 'shipment',
        })
        wiz_tariff_service.action_fetch_tariff()
        action['name'] = '{}: Fetch from {}'.format(self.name, str(ctx.get('tariff_type')).replace('_', ' ').title())
        action['domain'] = [('id', '=', wiz_tariff_service.id)]
        action['res_id'] = wiz_tariff_service.id
        return action
