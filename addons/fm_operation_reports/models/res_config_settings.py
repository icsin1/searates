# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_hbl_number = fields.Boolean(related='company_id.show_hbl_number', readonly=False)
    hbl_ir_field_id = fields.Many2one('ir.model.fields', related='company_id.hbl_ir_field_id', readonly=False)

    show_mbl_number = fields.Boolean(related='company_id.show_mbl_number', readonly=False)
    mbl_ir_field_id = fields.Many2one('ir.model.fields', related='company_id.mbl_ir_field_id', readonly=False)
    container_size_ids = fields.Many2many(related='company_id.container_size_ids', readonly=False)
    custom_duty_charge_ids = fields.Many2many(related="company_id.custom_duty_charge_ids",
                                              string="Custom Duty Charges", readonly=False)
