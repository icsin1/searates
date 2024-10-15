# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FreightShipmentTermsAndConditionsMixin(models.AbstractModel):
    _name = 'freight.shipment.terms.mixin'
    _description = 'Freight Shipment Terms Mixin'

    @api.model
    def _get_document_type_domain(self):
        return [('document_mode', '=', 'out'), ('report_template_ref_id', '!=', False)]

    document_type_id = fields.Many2one('freight.document.type', required=True, domain=_get_document_type_domain)
    terms_and_conditions = fields.Html()

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        for rec in self:
            if not rec.terms_and_conditions and rec.document_type_id.report_template_ref_id:
                rec.terms_and_conditions = rec.document_type_id.report_template_ref_id.terms_and_conditions
