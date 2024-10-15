# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    measurement_basis_id = fields.Many2one('freight.measurement.basis', required=False, default=lambda self: self.env.ref('freight_base.measurement_basis_shipment', raise_if_not_found=False))
    company_id = fields.Many2one('res.company', string='Company',  required=True, default=lambda self: self.env.company)
    standard_price = fields.Float(default=1.0, store=True)
    charge_type = fields.Selection(selection=[('destination', 'Destination'), ('freight', 'Freight'), ('origin', 'Origin'), ('other', 'Other')], default='other', tracking=True)

    _sql_constraints = [
        ('code_company_unique', 'UNIQUE(default_code,company_id)', 'Product Internal Reference must be Unique per Company!'),
    ]

    @api.model
    def get_import_templates(self):
        return self.env['base']._get_import_templates(self)

    @api.model
    def default_get(self, field_list):
        result = super(ProductTemplate, self).default_get(field_list)
        result['categ_id'] = self.env.ref('freight_base.shipment_charge_category').id
        return result

    @api.depends_context('company')
    @api.depends('product_variant_ids', 'product_variant_ids.standard_price')
    def _compute_standard_price(self):
        super(ProductTemplate, self)._compute_standard_price()
        # set default 1.0 instead of zero on record duplicate
        for template in self:
            template.standard_price = template.standard_price or 1.0

    @api.model
    def validate_prices(self, vals):
        if 'list_price' in vals:
            sale_price = vals['list_price']
            if sale_price <= 0:
                raise ValidationError(_('Sales Price must be more than 0.'))
        if 'standard_price' in vals:
            cost_price = vals['standard_price']
            if cost_price <= 0:
                raise ValidationError(_('Cost Price must be more than 0.'))

    @api.model
    def create(self, vals):
        self.validate_prices(vals)
        return super(ProductTemplate, self).create(vals)

    def write(self, vals):
        self.validate_prices(vals)
        return super(ProductTemplate, self).write(vals)
