from odoo import models, fields, api
import json

class FreightProductMixin(models.AbstractModel):
    _name = 'freight.product.mixin'
    _description = 'Freight Product Mixin'

    @api.depends('cargo_is_package_group', 'cargo_type_id')
    def _compute_packaging_mode(self):
        for rec in self:
            rec.packaging_mode = 'container' if not rec.cargo_is_package_group else 'package'

    @api.depends('transport_mode_id')
    def _compute_cargo_type_domain(self):
        for rec in self:
            if rec._name != 'freight.service.job':
                domain = [('transport_mode_id', '=', rec.transport_mode_id.id),
                          ('is_courier_shipment', '=', rec.is_courier_shipment)]
            else:
                domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.cargo_type_domain = json.dumps(domain)

    cargo_type_domain = fields.Char(compute='_compute_cargo_type_domain', store=True)

    def _compute_shipment_type_domain(self):
        for rec in self:
            domain = ['|', ('is_courier_shipment', '=', False), ('is_courier_shipment', '=', rec.is_courier_shipment)]
            rec.shipment_type_domain = json.dumps(domain)

    shipment_type_domain = fields.Char(compute='_compute_shipment_type_domain')

    transport_mode_id = fields.Many2one('transport.mode')
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    shipment_type_id = fields.Many2one('shipment.type')
    cargo_type_id = fields.Many2one('cargo.type')
    cargo_is_package_group = fields.Boolean(related='cargo_type_id.is_package_group', store=True)
    packaging_mode = fields.Selection([('container', 'Container'), ('package', 'Packages')], compute='_compute_packaging_mode', store=True)
