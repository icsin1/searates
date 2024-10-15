from odoo import models, fields, api


class FreightProxyConsigneeMixin(models.AbstractModel):
    _name = 'freight.proxy.consignee.mixin'
    _description = 'Freight Proxy Consignee Mixin'

    # Consignee
    proxy_consignee_id = fields.Many2one(
        'res.partner', string='Consignee', inverse='_inverse_consignee', domain="[('type', '=', 'contact'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    proxy_consignee_address_id = fields.Many2one(
        'res.partner', string='Consignee Address',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('parent_id', '=', proxy_consignee_id), ('id', '=', proxy_consignee_id)]")

    def _inverse_consignee(self):
        consignee_party = self.env.ref('freight_base.org_type_consignee', raise_if_not_found=False)
        if consignee_party:
            self.mapped('proxy_consignee_id').write({'category_ids': [(4, consignee_party.id)]})

    @api.onchange('proxy_consignee_id')
    def _onchange_proxy_consignee_id(self):
        for rec in self:
            if rec.proxy_consignee_id:
                addresses = self.proxy_consignee_id.get_default_addresses()
                rec.proxy_consignee_address_id = addresses and addresses[0]
