
from odoo import models, fields, api


class FreightHouseShipmentPackage(models.Model):
    _inherit = 'freight.house.shipment.package'

    def _get_cfs_domain(self):
        return [('location_type_id', '=', self.env.ref('fm_road.location_type_cfs').id)]

    stuffing_cfs_id = fields.Many2one("freight.un.location", string="CFS", domain=_get_cfs_domain)
    destuffing_cfs_id = fields.Many2one("freight.un.location", string="CFS", domain=_get_cfs_domain)
    allowed_truck_number_ids = fields.Many2many('freight.truck.number', compute='_compute_allowed_truck_number_ids')
    allowed_truck_trailer_number_ids = fields.Many2many('freight.truck.trailer.number',
                                                        compute='_compute_truck_trailer_number_ids')

    @api.depends('shipment_id.transportation_detail_ids', 'truck_number_id')
    def _compute_truck_trailer_number_ids(self):
        for rec in self:
            transportation_detail_ids = rec.shipment_id.transportation_detail_ids\
                .filtered(lambda t: t.truck_number_id == rec.truck_number_id)
            rec.allowed_truck_trailer_number_ids = transportation_detail_ids.mapped('trailer_number_id')

    @api.depends('shipment_id.transportation_detail_ids')
    def _compute_allowed_truck_number_ids(self):
        for rec in self:
            domain = [
                '|',
                ('id', 'in', rec.shipment_id.transportation_detail_ids.mapped('truck_number_id.id')),
                ('house_shipment_package_ids', 'in', rec.ids)
            ]
            rec.allowed_truck_number_ids = self.env['freight.truck.number'].search(domain)

    def _inverse_truck_number_id(self):
        for record in self:
            if record.shipment_id and record.shipment_id.mode_type == "land" and record.truck_number_id and record.container_number:
                transportation_id = record.shipment_id.transportation_detail_ids\
                    .filtered(lambda t: t.truck_number_id == record.truck_number_id and t
                              .container_type_id == record.container_type_id and not t.container_number_id)
                if transportation_id:
                    transportation_id = transportation_id[0]
                    transportation_id.container_number_id = record.container_number
