# -*- coding: utf-8 -*-
from odoo import models, fields


class FreightChargeMixin(models.AbstractModel):
    _inherit = 'mixin.freight.charge'

    company_calculate_tds = fields.Boolean(related='company_id.calculate_tds', store=True)
