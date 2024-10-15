from odoo import models, fields, api


class UoM(models.Model):
    _inherit = 'uom.uom'

    transport_mode_ids = fields.Many2many('transport.mode', 'transport_mode_uom_uom', string='Transport Mode')

    @api.model
    def set_uom_transport_mode(self):
        air_pack_uom = self.search(['|', ('name', '=', 'BAG (Bag)'), ('name', '=', 'BDL (Bundle)'), ('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)])
        if air_pack_uom:
            air_pack_uom.write({'transport_mode_ids': [(6, 0, self.env.ref('freight_base.transport_mode_air').ids)]})
        other_pack_uom = self.search([('name', '!=', 'BAG (Bag)'), ('name', '!=', 'BDL (Bundle)'), ('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)])
        if other_pack_uom:
            other_pack_uom.write({'transport_mode_ids': [(6, 0, [self.env.ref('freight_base.transport_mode_sea').id, self.env.ref('freight_base.transport_mode_land').id])]})
