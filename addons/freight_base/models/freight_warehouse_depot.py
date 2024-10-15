# -*- coding: utf-8 -*-

from odoo import models, fields


class FreightWarehouseDepot(models.Model):
    _name = 'freight.warehouse.depot'
    _description = 'Warehouse Depot'
    _rec_name = 'depot_name'

    wd_type = fields.Selection([
        ('depot', 'Depot'),
        ('warehouse', 'Warehouse'),
    ], string='Type', required=True)
    depot_name = fields.Char(string='Name', required=True)
    depot_code = fields.Char(string='Code', required=True)
    depot_name_local = fields.Char(string='Name (Local)')
    freight_port_id = fields.Many2one('freight.port', string='Port Name')
    nation = fields.Char(string='Nation')
    operator = fields.Char(string='Operator')
    pic = fields.Char(string='PIC')
    door = fields.Integer(string='Door')
    is_external_yard = fields.Boolean(string="Is external Yard")
    additional_details = fields.Text(string='Addtional Details')
