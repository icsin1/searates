# -*- coding: utf-8 -*-
from odoo import models, fields, api
from ..models import freight_house_shipment


ROAD_EXPORT_STATE = [(key, value) for key, value in freight_house_shipment.HOUSE_STATE if key not in ['nomination_generated', 'hbl_generated', 'hawb_generated']]


class WizardHouseShipmentStatus(models.TransientModel):
    _inherit = 'wizard.house.shipment.status'

    road_export_state = fields.Selection(ROAD_EXPORT_STATE)

    @api.depends('import_state', 'export_state', 'cross_state', 'shipment_type_key',
                 'domestic_export_state', 'road_export_state')
    def _compute_state(self):
        super()._compute_state()
        for wizard in self:
            if wizard.shipment_type_key == 'export' and wizard.shipment_id.mode_type == "land":
                wizard.state = wizard.road_export_state
