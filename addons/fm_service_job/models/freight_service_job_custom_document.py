from odoo import models, fields


class FreightServiceJobCustomsDocument(models.Model):
    _name = 'freight.service.job.customs.document'
    _description = 'Service Job Customs Document'

    name = fields.Char('Document Name')
    service_job_id = fields.Many2one('freight.service.job', required=True, ondelete='cascade')

    # Custom Attributes
    declaration_date = fields.Date('Declaration Date')
    declaration_number = fields.Char('Declaration No.')
    customs_clearance_datetime = fields.Datetime(string='Clearance Date & Time')
    note = fields.Char(string='Note')
    document_file = fields.Binary(string='Documents')
    file_name = fields.Char(string='File Name')
