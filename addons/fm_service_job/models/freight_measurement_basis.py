# -*- coding: utf-8 -*-
from odoo import models, fields


class FreightMeasurementBasis(models.Model):
    _inherit = 'freight.measurement.basis'

    is_job_measurement = fields.Boolean()
