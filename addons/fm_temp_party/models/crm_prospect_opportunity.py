# -*- coding: utf-8 -*-
from odoo import models, fields


class Opportunity(models.Model):
    _inherit = "crm.prospect.opportunity"

    enable_temp_party = fields.Boolean('Enable Temporary Party', related='company_id.enable_temp_party', help='Enable to enter Temporary Name and Address', store=True)
    temp_party_name = fields.Char('Temporary Party Name')
    temp_party_address = fields.Text('Temporary Party Address')

    def action_create_get_partner(self):
        self.ensure_one()
        if self.enable_temp_party:
            return self.env['res.partner']
        else:
            return super().action_create_get_partner()

    def _prepare_quotation_vals(self):
        self.ensure_one()
        quote_vals = super()._prepare_quotation_vals()
        if self.customer_type == 'consignor':
            quote_vals['default_temp_shipper_name'] = self.temp_party_name
            quote_vals['default_temp_shipper_address'] = self.temp_party_address
        elif self.customer_type == 'consignee':
            quote_vals['default_temp_consignee_name'] = self.temp_party_name
            quote_vals['default_temp_consignee_address'] = self.temp_party_address
        return quote_vals
