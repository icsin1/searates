# -*- coding: utf-8 -*-

from odoo import fields, models


class FreightVesselCategory(models.Model):
    _name = "freight.vessel.category"
    _description = 'Freight Vessel Category'

    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
