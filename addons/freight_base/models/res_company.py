# -*- coding: utf-8 -*-
import pytz
from odoo import fields, models, api, _
from odoo.addons.base.models.res_partner import _tz_get
from odoo.exceptions import ValidationError
import re


class ResCompany(models.Model):
    _inherit = 'res.company'

    pickup_product_id = fields.Many2one('product.product', string='Pickup Type', check_company=True)
    on_carriage_product_id = fields.Many2one('product.product', string='On Carriage Type', check_company=True)
    pre_carriage_product_id = fields.Many2one('product.product', string='Pre Carriage Type', check_company=True)
    delivery_product_id = fields.Many2one('product.product', string='Delivery Type', check_company=True)

    pack_uom_id = fields.Many2one(
        'uom.uom', string="Packs UOM", domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)])
    weight_uom_id = fields.Many2one(
        'uom.uom', string="Weight UOM", domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)],
        default=lambda self: self.env.ref('uom.product_uom_kgm', raise_if_not_found=False))
    volume_uom_id = fields.Many2one(
        'uom.uom', string="Volume UOM", domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)],
        default=lambda self: self.env.ref('uom.product_uom_cubic_meter', raise_if_not_found=False))
    dimension_uom_id = fields.Many2one(
        'uom.uom', string="Dimension UOM", domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)],
        default=lambda self: self.env.ref('uom.product_uom_cm', raise_if_not_found=False))
    container_size_ids = fields.Many2many('freight.container.type.size', string='Container Size')
    show_contact_prefix = fields.Boolean(copy=False, default=True)

    @api.constrains('doc_file_size')
    def check_file_limit(self):
        if self.doc_file_size > 50:
            raise ValidationError('Maximum file size is 50 MB')

    @api.model
    def set_default_timezone(self):
        tz = self.env.user.tz or 'UTC'
        if self.country_id:
            tz = pytz.country_timezones.get(self.country_id.code, ['UTC'])[0]
        return tz

    def _set_default_products(self, company):
        product_list = {
            'pickup_product_id': {'name': _('Pickup'), 'default_code': 'PU'},
            'on_carriage_product_id': {'name': _('On Carriage'), 'default_code': 'OCAG'},
            'pre_carriage_product_id': {'name': _('Pre Carriage'), 'default_code': 'PCAG'},
            'delivery_product_id': {'name': _('Delivery'), 'default_code': 'DL'},
        }
        values = {}
        # Set default value for service type mapping
        shipment_charge = self.env.ref('freight_base.shipment_charge_category', raise_if_not_found=False)
        product_vals = {
            'detailed_type': 'service',
            'categ_id': shipment_charge and shipment_charge.id,
            'company_id': company.id,
        }
        ProductProduct = self.env['product.product'].sudo()

        for field_name, product_values in product_list.items():
            product_vals['default_code'] = "{}-{}".format(company.code, product_values.get('default_code'))
            product = ProductProduct.create({**product_values, **product_vals})
            values[field_name] = product.id
        return values

    @api.model_create_single
    def create(self, vals):
        res = super(ResCompany, self.with_context(create_company=True)).create(vals)
        res.write(self._set_default_products(res))
        res.sudo()._create_per_company_freight_sequence()
        return res

    @api.onchange('email')
    def validate_mail(self):
        if self.email:
            match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,5})$', str(self.email).lower())
            if not match:
                raise ValidationError('Not a valid E-mail ID')

    volumetric_divider_value = fields.Integer(default=5000)
    doc_file_size = fields.Integer(string="File Size Upto", default=5)
    code = fields.Char(string='Code')
    un_location_id = fields.Many2one('freight.un.location', string='Un/Locode')
    tz = fields.Selection(_tz_get, string='Time Zone', default=set_default_timezone)
    customs_reg_number = fields.Char(string='Customs Registration Number')
    agent_iata_code = fields.Char(string='Agent IATA Code')
    agent_iata_number = fields.Char(string='Agent IATA Number')
    date_of_incorporation = fields.Date(string='Date of Incorporation')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', "Company Code must be unique.")
    ]

    @api.onchange('country_id')
    def _onchange_country_id(self):
        for rec in self:
            tz = False
            if rec.country_id:
                tz = pytz.country_timezones.get(rec.country_id.code, ['UTC'])[0]
            rec.tz = tz

    def _create_per_company_freight_sequence(self):
        self.ensure_one()
