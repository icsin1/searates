# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightHSNMaster(models.Model):
    _name = "freight.hsn.master"
    _description = 'HSN Master'

    name = fields.Char('HSN Code', required=True)
    hsn_name = fields.Char('HSN Name',)
    govt_code = fields.Char('Govt Notified HSN Code')
    govt_category_name = fields.Char('Category Name Spec by Govt')
    vendor_tax_id = fields.Many2one('account.tax', 'Vendor Tax', domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]")
    customer_tax_id = fields.Many2one('account.tax', 'Customer Tax',  domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'sale')]")
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if self.search_count([('name', '=', rec.name)]) > 1:
                raise ValidationError(_("HSN Code:%s already exists in the system!") % (rec.name))
