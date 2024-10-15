# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pickup_product_id = fields.Many2one(
        'product.product', string='Pickup Type', readonly=False, related='company_id.pickup_product_id')
    on_carriage_product_id = fields.Many2one(
        'product.product', string='On Carriage Type', readonly=False, related='company_id.on_carriage_product_id')
    pre_carriage_product_id = fields.Many2one(
        'product.product', string='Pre Carriage Type', readonly=False, related='company_id.pre_carriage_product_id')
    delivery_product_id = fields.Many2one(
        'product.product', string='Delivery Type', readonly=False, related='company_id.delivery_product_id')
    volumetric_weight_divided_value = fields.Integer(string='Volumetric Divided Value', readonly=False, related='company_id.volumetric_divider_value')

    pack_uom_id = fields.Many2one(
        'uom.uom', related="company_id.pack_uom_id", string="Packs UOM", readonly=False, domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)])
    weight_uom_id = fields.Many2one(
        'uom.uom', related="company_id.weight_uom_id", string="Weight UOM", readonly=False, domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])
    volume_uom_id = fields.Many2one(
        'uom.uom', related="company_id.volume_uom_id", string="Volume UOM", readonly=False, domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)])
    dimension_uom_id = fields.Many2one(
        'uom.uom', related="company_id.dimension_uom_id", string="Dimension UOM", readonly=False, domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)])

    doc_file_size = fields.Integer(string="File Size Upto", related='company_id.doc_file_size', readonly=False)
    max_document_history = fields.Integer(string="Max Document History", config_parameter='freight_base.max_document_history', default=1)

    # Module to manage Freight Costs as Expense in accounting instead of vendor bills
    module_fm_account_expense_entry = fields.Boolean(default=False)
    show_contact_prefix = fields.Boolean(related='company_id.show_contact_prefix', readonly=False)

    def execute(self):
        res = super().execute()
        partner_ids = self.env['res.partner'].search([
            '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)])
        for partner in partner_ids:
            partner._compute_display_name()
        return res
