# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hsn_charge_ids = fields.One2many('freight.hsn.charges', 'charge_id', string='HSN Mapping')
    country_id = fields.Many2one('res.country', 'Country', related='company_id.country_id')
