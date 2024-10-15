# -*- coding: utf-8 -*-

from odoo import models


class Opportunity(models.Model):
    _inherit = "crm.prospect.opportunity"

    def action_create_quotation(self):
        self.ensure_one()
        action = super().action_create_quotation()
        action['context'].update({
            'default_pickup_location_type_id': self.pickup_location_type_id.id,
            'default_delivery_location_type_id': self.delivery_location_type_id.id,
            'default_pickup_zipcode': self.pickup_zipcode,
            'default_delivery_zipcode': self.delivery_zipcode,
        })
        return action
