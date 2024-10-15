# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_service_job_categ = fields.Boolean(related='categ_id.is_service_job_categ')

    @api.onchange('categ_id', 'measurement_basis_id')
    @api.constrains('categ_id', 'measurement_basis_id')
    def _check_categ_measurement(self):
        job_categ = self.env.ref('fm_service_job.job_charge_category', raise_if_not_found=False)
        job_measurement_basis = self.env['freight.measurement.basis'].search([('is_job_measurement', '=', True)])
        for charge in self:
            if charge.categ_id and charge.measurement_basis_id and charge.categ_id == job_categ and not charge.measurement_basis_id.is_job_measurement:
                charge.measurement_basis_id = ''
                return {
                    'warning': {
                        'title': _('Service Job Measurement-Basis'),
                        'message': _("Service Job can only have '%s' Measurement basis.") % (','.join(job_measurement_basis.mapped('name')))
                        },
                    }
