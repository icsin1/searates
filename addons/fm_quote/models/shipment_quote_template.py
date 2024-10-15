# -*- coding: utf-8 -*-

from odoo import fields, models, api
import json

class QuoteTemplate(models.Model):
    _name = "shipment.quote.template"
    _description = "Quote Template"

    @api.depends('transport_mode_id')
    def _compute_cargo_type_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.cargo_type_domain = json.dumps(domain)

    cargo_type_domain = fields.Char(compute='_compute_cargo_type_domain', store=True)

    name = fields.Char(required=True)
    body_html = fields.Html('Content', translate=True, required=True)
    transport_mode_id = fields.Many2one('transport.mode', string='Transport Mode')
    shipment_type_id = fields.Many2one('shipment.type', string='Shipment Type')
    cargo_type_ids = fields.Many2many('cargo.type', 'quote_template_cargo_type_rel', 'quote_template_id', 'cargo_type_id', string='Cargo Type')
    template_for = fields.Selection([('shipment', 'Shipment')], string='Type', default='shipment')

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        if not self.env.context.get('cargo_type_ids'):
            self.cargo_type_ids = False

    @api.onchange('template_for')
    def _onchange_template_for(self):
        fields = ['transport_mode_id', 'shipment_type_id', 'cargo_type_ids']
        if self.template_for != 'shipment':
            self.update({field: False for field in fields})
        return {}

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('cargo_type_ids'):
            res['cargo_type_ids'] = [(6, 0, [self.env.context.get('cargo_type_ids')])]
        return res
