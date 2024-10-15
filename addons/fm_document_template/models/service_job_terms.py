from odoo import models, fields, api
import json


class FreightServiceJobTerms(models.Model):
    _inherit = 'freight.service.job.terms'

    def get_service_document_template_domain(self):
        self.ensure_one()
        return json.dumps([('document_type_id', '=', self.document_type_id.id), ('service_job_type_id', '=', self.service_job_id.service_job_type_id.id)])

    @api.depends('service_job_id.service_job_type_id', 'document_type_id')
    def _compute_service_document_template_domain(self):
        for service in self:
            service.service_template_domain = service.get_service_document_template_domain()

    document_template_id = fields.Many2one('shipment.document.template', required=True, string='Document Template')
    service_template_domain = fields.Char(compute='_compute_service_document_template_domain')

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
