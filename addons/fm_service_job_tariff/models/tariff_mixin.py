# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TariffMixin(models.AbstractModel):
    _inherit = 'tariff.mixin'

    tariff_for = fields.Selection(selection_add=[('job', 'Service Job')])
    service_job_type_id = fields.Many2one('freight.job.type', ondelete='restrict')

    @api.onchange('tariff_for')
    def _onchange_tariff_for(self):
        if self.tariff_for == 'job':
            self.update({
                'transport_mode_id': False,
                'shipment_type_id': False,
                'cargo_type_id': False,
                'line_ids': False
            })
        if self.tariff_for != 'job':
            self.update({'service_job_type_id': False,
                         'line_ids': False})
