# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.portal.controllers import portal


class PortalShipmentDashboard(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(PortalShipmentDashboard, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        freight_house_shipment_obj = request.env['freight.house.shipment']
        if 'ff_jobs_shipment_count' in counters:
            values['ff_jobs_shipment_count'] = freight_house_shipment_obj.search_count(self._prepare_ff_house_shipment_domain(partner)) \
                if freight_house_shipment_obj.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_ff_house_shipment_domain(self, partner):
        return [('client_id', '=', partner.id), ('state', 'in', ['booked', 'in_transit', 'arrived', 'completed'])]

    def _prepare_service_jobs_shipment_domain(self, partner):
        return [('client_id', '=', partner.id)]
