from odoo import models, api, fields


class FreightHouseShipmentPackage(models.Model):
    _inherit = 'freight.house.shipment.package'

    quote_transport_line_id = fields.Many2one('quote.transportation.package.details', copy=False)

    @api.depends('shipment_id', 'container_type_id')
    def _compute_allow_container_number(self):
        super(FreightHouseShipmentPackage, self)._compute_allow_container_number()
        for rec in self:
            container_number_ids = rec.allow_container_number_ids  # Get the existing container numbers from the super call
            transportation_detail_ids = rec.shipment_id.transportation_detail_ids.filtered(
                lambda t: t.truck_number_id == rec.truck_number_id
            )
            additional_container_numbers = transportation_detail_ids.mapped('container_number_id').ids
            container_number_ids |= self.env['freight.master.shipment.container.number'].browse(additional_container_numbers)
            rec.allow_container_number_ids = [(6, False, container_number_ids.ids)]

    @api.model_create_single
    def create(self, values):
        package = super().create(values)
        # set packages/Container reference from shipment to quote
        if package.quote_transport_line_id:
            package.quote_transport_line_id.pack_container_id = package.id
        return package
