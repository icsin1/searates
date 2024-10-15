from odoo import models, fields, api


class FreightProxyShipperMixin(models.AbstractModel):
    _name = 'freight.proxy.shipper.mixin'
    _description = 'Freight Proxy Shipper Mixin'

    # Shipper
    proxy_shipper_id = fields.Many2one(
        'res.partner', string='Shipper', inverse='_inverse_shipper', domain="[('type', '=', 'contact'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    proxy_shipper_address_id = fields.Many2one(
        'res.partner', string='Shipper Address', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('parent_id', '=', proxy_shipper_id), ('id', '=', proxy_shipper_id)]")

    def _inverse_shipper(self):
        shipper_party = self.env.ref('freight_base.org_type_shipper', raise_if_not_found=False)
        if shipper_party:
            self.mapped('proxy_shipper_id').write({'category_ids': [(4, shipper_party.id)]})

    @api.onchange('proxy_shipper_id')
    def _onchange_proxy_shipper_id(self):
        for rec in self:
            if rec.proxy_shipper_id:
                addresses = self.proxy_shipper_id.get_default_addresses()
                rec.proxy_shipper_address_id = addresses and addresses[0]
