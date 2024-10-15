from odoo import models, fields


class FreightMeasurementBasis(models.Model):
    _name = 'freight.measurement.basis'
    _description = 'Freight Measurement Basis'
    _order = 'sequence'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=0)
    active = fields.Boolean(default=True)
    package_group = fields.Selection([('all', 'All'), ('package', 'Package'), ('container', 'Container')], string='Package Group')
    transport_mode_ids = fields.Many2many('transport.mode', 'transport_mode_freight_measurement_basis', string='Transport Mode')
