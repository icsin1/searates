# -*- coding: utf-8 -*-

from odoo import models


class FreightHouseShipmentPortal(models.Model):
    _name = 'freight.house.shipment'
    _inherit = ['freight.house.shipment', 'portal.mixin']

    def _get_portal_return_action(self):
        """ Return the action used to display orders when returning from customer portal. """
        self.ensure_one()
        return self.env.ref('freight_management.freight_shipment_house_action')

    def get_ff_portal_url(self):
        """ return url for FF Job shipment to open record"""
        self.ensure_one()
        url = '/dashboard/ff_jobs_shipment/' + '%s?access_token=%s' % (
            self.id, self._portal_ensure_token(),
        )
        return url

    def get_service_portal_url(self):
        """ return url for Service Job shipment to open record"""
        self.ensure_one()
        url = '/dashboard/service_jobs_shipment/' + '%s?access_token=%s' % (
            self.id, self._portal_ensure_token(),
        )
        return url
