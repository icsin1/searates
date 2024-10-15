# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.portal.controllers import portal


class PortalShipmentDashboard(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(PortalShipmentDashboard, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        freight_service_job_obj = request.env['freight.service.job']
        if 'service_jobs_shipment_count' in counters:
            values['service_jobs_shipment_count'] = freight_service_job_obj.search_count(self._prepare_service_jobs_shipment_domain(partner)) \
                if freight_service_job_obj.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_service_jobs_shipment_domain(self, partner):
        return [('client_id', '=', partner.id)]
