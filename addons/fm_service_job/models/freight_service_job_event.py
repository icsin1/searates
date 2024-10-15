from odoo import models, fields


class FreightServiceJobEvent(models.Model):
    _name = 'freight.service.job.event'
    _inherit = ['freight.shipment.event.mixin']
    _description = 'Service Job Milestone'

    service_job_id = fields.Many2one('freight.service.job', required=True, ondelete='cascade')
