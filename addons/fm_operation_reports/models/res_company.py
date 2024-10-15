# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    show_hbl_number = fields.Boolean(string='HBL Number')
    hbl_ir_field_id = fields.Many2one('ir.model.fields', string='HBL Field', domain=lambda self: [
        ('model_id', '=', self.env.ref('freight_management.model_freight_house_shipment').id),
        ('ttype', '=', 'char'), ('store', '=', True)])

    show_mbl_number = fields.Boolean(string='MBL Number')
    mbl_ir_field_id = fields.Many2one('ir.model.fields', string='MBL Field', domain=lambda self: [
        ('model_id', '=', self.env.ref('freight_management.model_freight_master_shipment').id),
        ('ttype', '=', 'char'), ('store', '=', True)])
    custom_duty_charge_ids = fields.Many2many('product.product', string="Custom Duty Charges")
