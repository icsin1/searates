# -*- coding: utf-8 -*-

from odoo import fields, models, api
import json


class DocumentTemplate(models.Model):
    _name = "shipment.document.template"
    _description = "Document Template"

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
    cargo_type_id = fields.Many2one('cargo.type', string='Cargo Type')
    document_template_for = fields.Selection([('shipment', 'Shipment'), ('job', 'Service Job')], string='Type', default='shipment')
    document_type_id = fields.Many2one('freight.document.type', string='Document Type')
    service_job_type_id = fields.Many2one('freight.job.type', ondelete='restrict')

    @api.depends('document_type_id')
    def _compute_document_mode_domain(self):
        for rec in self:
            domain = [('document_mode', '=', 'out')]
            rec.document_mode_domain = json.dumps(domain)

    document_mode_domain = fields.Char(compute='_compute_document_mode_domain', store=True)

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        if not self.env.context.get('cargo_type_id'):
            self.cargo_type_id = False

    @api.onchange('document_template_for')
    def _onchange_document_template_for(self):
        if self.document_template_for != 'shipment':
            self.update({'transport_mode_id': False,
                         'shipment_type_id': False,
                         'cargo_type_id': False, })
        if self.document_template_for != 'job':
            self.update({'service_job_type_id': False})
        return {}
