# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ShipmentQuoteTemplate(models.Model):
    _inherit = 'shipment.quote.template'

    template_for = fields.Selection(selection_add=[('job', 'Service Job')])
    service_job_type_id = fields.Many2one('freight.job.type', ondelete='restrict')

    @api.onchange('template_for')
    def _onchange_template_for(self):
        result = super()._onchange_template_for()
        if self.template_for != 'job':
            self.update({'service_job_type_id': False})
        return result
