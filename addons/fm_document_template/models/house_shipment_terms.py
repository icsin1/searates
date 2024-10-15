from odoo import models, fields, api
import json


class FreightHouseShipmentTerms(models.Model):
    _inherit = 'freight.house.shipment.terms'

    def get_house_document_template_domain(self):
        self.ensure_one()
        return json.dumps([('document_template_for', '=', 'shipment'), ('document_type_id', '=', self.document_type_id.id), ('transport_mode_id', '=', self.shipment_id.transport_mode_id.id),
                           ('shipment_type_id', '=', self.shipment_id.shipment_type_id.id), ('cargo_type_id', '=', self.shipment_id.cargo_type_id.id)])

    @api.depends('shipment_id.shipment_for', 'shipment_id.transport_mode_id', 'shipment_id.shipment_type_id', 'shipment_id.cargo_type_id', 'document_type_id')
    def _compute_house_document_template_domain(self):
        for house in self:
            house.house_template_domain = house.get_house_document_template_domain()

    document_template_id = fields.Many2one('shipment.document.template', required=True, string='Document Template')
    house_template_domain = fields.Char(compute='_compute_house_document_template_domain')

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        super()._onchange_document_type_id()
        for rec in self:
            rec.document_template_id = False
            if rec.document_type_id:
                rec.document_template_id = True

    @api.onchange('document_template_id')
    def _onchange_document_template_id(self):
        self.terms_and_conditions = False
        if self.document_template_id:
            self.terms_and_conditions = self.document_template_id.body_html
