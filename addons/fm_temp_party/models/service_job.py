# -*- coding: utf-8 -*-
from odoo import models, fields


class ServiceJob(models.Model):
    _inherit = "freight.service.job"

    enable_temp_party = fields.Boolean('Enable Temporary Party', related='company_id.enable_temp_party',
                                       help='Enable to enter Temporary Name and Address', store=True)
    temp_shipper_name = fields.Char('Shipper')
    temp_shipper_address = fields.Text('Shipper Address')
    temp_consignee_name = fields.Char('Consignee')
    temp_consignee_address = fields.Text('Consignee Address')
