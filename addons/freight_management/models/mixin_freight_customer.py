from odoo import models, fields, api


class FreightCustomerMixin(models.AbstractModel):
    _name = 'freight.customer.mixin'
    _description = 'Freight Customer Mixin'

    # Customer
    client_id = fields.Many2one(
        'res.partner', context="{'default_type': 'contact'}", inverse='_inverse_client', string='Customer',
        domain="[('type', '=', 'contact'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", required=True)
    client_address_id = fields.Many2one(
        'res.partner',
        string='Client Address',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('parent_id', '=', client_id), ('id', '=', client_id)]")

    def _inverse_client(self):
        customer_party = self.env.ref('freight_base.org_type_customer', raise_if_not_found=False)
        if customer_party:
            self.mapped('client_id').write({'category_ids': [(4, customer_party.id)]})

    @api.onchange('client_id')
    def _onchange_client_id(self):
        for rec in self:
            if rec.client_id:
                addresses = self.client_id.get_default_addresses()
                rec.client_address_id = addresses and addresses[0]
