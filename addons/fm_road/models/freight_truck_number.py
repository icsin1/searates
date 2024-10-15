# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class FreightTruckNumber(models.Model):
    _name = "freight.truck.number"
    _description = 'Freight Truck Number'
    _rec_name = 'vehicle_registration_number'

    vehicle_registration_number = fields.Char(required=True, copy=False, default=_("New"))
    chassis_number = fields.Char()
    engine_number = fields.Char()
    truck_owned_by = fields.Selection([('internal', 'Internal'), ('external', 'External')], required=True, default="internal", string='Truck Owned By')
    truck_type_id = fields.Many2one('truck.type')

    @api.constrains('vehicle_registration_number')
    def _check_vehicle_registration_number(self):
        for rec in self:
            other_truck_number = self.search([('vehicle_registration_number', '=ilike', rec.vehicle_registration_number), ('id', '!=', rec.id)], limit=1)
            if other_truck_number:
                raise ValidationError(_("Vehicle Registration Number:%s already exists in the system!") % (other_truck_number.vehicle_registration_number))
