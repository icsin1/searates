from odoo import models, fields, api


class FreightMasterShipmentRoute(models.Model):
    _name = 'freight.quote.route'
    _description = 'Quote route'
    _inherit = ['freight.shipment.route.mixin']

    quote_id = fields.Many2one('shipment.quote', required=True, ondelete='cascade')
    transport_mode_id = fields.Many2one(related='quote_id.transport_mode_id', store=True, string='Shipment Transport')
    name = fields.Char("Route Desc", compute="_compute_route_name", store=True)
    shipper_id = fields.Many2one('res.partner', "Shipper")
    consignee_id = fields.Many2one('res.partner', "Consignee")
    container_no = fields.Many2one('freight.master.shipment.container.number', "Container No")
    customs_seal_number = fields.Char(related='container_no.customs_seal_number', store=True)

    _sql_constraints = [
        ('shipment_charge_location_unique', 'CHECK(1=1)', 'IGNORING CONSTRAINT!')
    ]

    @api.onchange('route_type')
    def _onchange_route_type(self):
        if self.route_type == 'x-stuff':
            self.transport_mode_id = self.env.ref('freight_base.transport_mode_sea').id
        else:
            self.transport_mode_id = self.env.ref('freight_base.transport_mode_land').id

    @api.depends('route_type', 'from_location_id', 'to_location_id', 'transport_mode_type')
    def _compute_route_name(self):
        for rec in self:
            rec.name = '{}-{}'.format('M', rec.get_route_prefix_value())
