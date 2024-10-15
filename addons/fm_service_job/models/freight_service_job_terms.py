from odoo import models, fields, api


class FreightServiceJobTerms(models.Model):
    _name = 'freight.service.job.terms'
    _inherit = 'freight.shipment.terms.mixin'
    _description = 'Service Job Terms'
    _rec_name = 'service_job_id'

    @api.model
    def _get_document_type_domain(self):
        return super()._get_document_type_domain() + [('model_id.model', '=', 'freight.service.job')]

    service_job_id = fields.Many2one('freight.service.job', ondelete='cascade', required=True)
    document_type_id = fields.Many2one('freight.document.type', required=True, domain=_get_document_type_domain)

    _sql_constraints = [
        ('document_type_and_service_job_unique', 'UNIQUE(document_type_id,service_job_id)', "Document Type already exists.")
    ]
