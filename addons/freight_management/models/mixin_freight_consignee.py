from odoo import models, fields, api


class FreightConsigneeMixin(models.AbstractModel):
    _name = 'freight.consignee.mixin'
    _description = 'Freight Consignee Mixin'

    # Consignee
    consignee_id = fields.Many2one(
        'res.partner', string='Consignee', inverse='_inverse_consignee', domain="[('type', '=', 'contact'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    consignee_address_id = fields.Many2one(
        'res.partner', string='Consignee Address', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('parent_id', '=', consignee_id), ('id', '=', consignee_id)]")

    def _inverse_consignee(self):
        consignee_party = self.env.ref('freight_base.org_type_consignee', raise_if_not_found=False)
        if consignee_party:
            self.mapped('consignee_id').write({'category_ids': [(4, consignee_party.id)]})

    @api.onchange('consignee_id')
    def _onchange_consignee_id(self):
        for rec in self:
            if rec.consignee_id:
                addresses = self.consignee_id.get_default_addresses()
                rec.consignee_address_id = addresses and addresses[0]
