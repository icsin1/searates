from odoo import models, fields, api


class FreightShipperMixin(models.AbstractModel):
    _name = 'freight.shipper.mixin'
    _description = 'Freight Shipper Mixin'

    # Shipper
    shipper_id = fields.Many2one(
        'res.partner', string='Shipper', inverse='_inverse_shipper', domain="[('type', '=', 'contact'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    shipper_address_id = fields.Many2one(
        'res.partner', string='Shipper Address', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('parent_id', '=', shipper_id), ('id', '=', shipper_id)]")

    def _inverse_shipper(self):
        shipper_party = self.env.ref('freight_base.org_type_shipper', raise_if_not_found=False)
        if shipper_party:
            self.mapped('shipper_id').write({'category_ids': [(4, shipper_party.id)]})

    @api.onchange('shipper_id')
    def _onchange_shipper_id(self):
        for rec in self:
            if rec.shipper_id:
                addresses = self.shipper_id.get_default_addresses()
                rec.shipper_address_id = addresses and addresses[0]
