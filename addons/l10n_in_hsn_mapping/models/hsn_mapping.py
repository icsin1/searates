# -*- coding: utf-8 -*-

import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HSNCharges(models.Model):
    _name = 'freight.hsn.charges'
    _description = 'HSN Mapping'

    @api.depends('transport_mode_id')
    def _compute_cargo_type_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.cargo_type_domain = json.dumps(domain)

    cargo_type_domain = fields.Char(compute='_compute_cargo_type_domain', store=True)
    charge_id = fields.Many2one('product.template', 'Charge Master')
    hsn_id = fields.Many2one('freight.hsn.master', 'HSN Master')
    transport_mode_id = fields.Many2one('transport.mode',)
    shipment_type_id = fields.Many2one("shipment.type", string="Shipment Type")
    cargo_type_id = fields.Many2one('cargo.type', string="Cargo Type")
    hsn_name = fields.Char('HSN Name', related='hsn_id.hsn_name')
    vendor_tax_id = fields.Many2one('account.tax', related='hsn_id.vendor_tax_id')
    customer_tax_id = fields.Many2one('account.tax', related='hsn_id.customer_tax_id')
    effective_date = fields.Date('Effective Date')

    @api.constrains('transport_mode_id', 'shipment_type_id', 'cargo_type_id', 'charge_id', 'effective_date')
    def _check_name(self):
        for rec in self:
            if self.search_count([('transport_mode_id', '=', rec.transport_mode_id.id), ('shipment_type_id', '=', rec.shipment_type_id.id), ('cargo_type_id', '=', rec.cargo_type_id.id),
                                  ('charge_id', '=', rec.charge_id.id), ('effective_date', '=', rec.effective_date)]) > 1:
                raise ValidationError(_("HSN Mapping for Charge Master in Same Date already exists in the system!"))

    @api.onchange('transport_mode_id')
    def onchange_transport_mode(self):
        for rec in self:
            if rec.cargo_type_id.transport_mode_id != rec.transport_mode_id:
                rec.cargo_type_id = False
