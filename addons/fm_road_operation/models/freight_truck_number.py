# -*- coding: utf-8 -*-

from odoo import fields, models, api


class FreightTruckNumber(models.Model):
    _inherit = "freight.truck.number"

    @api.depends('house_shipment_package_ids', 'house_shipment_package_ids.shipment_id.state')
    def _compute_status(self):
        for rec in self:
            status = "unused"
            house_shipments = rec.house_shipment_package_ids.mapped('shipment_id')
            if (house_shipments and house_shipments.filtered(
                    lambda hs: hs.state not in ('created', 'cancelled'))):
                status = "used"
            elif rec.house_shipment_package_ids:
                status = "linked"
            rec.status = status

    status = fields.Selection([('unused', 'Unused'), ('used', 'Used'), ('linked', 'Linked')],
                              compute="_compute_status", store=True)
    house_shipment_package_ids = fields.One2many('freight.house.shipment.package', 'truck_number_id',
                                                 string='House Shipment Packages')
    master_shipment_package_ids = fields.One2many('freight.master.shipment.package', 'truck_number_id',
                                                  string='Master Shipment Packages')
