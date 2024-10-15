# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_membership_multi = fields.Boolean(string='Multi Teams', config_parameter='fm_sale_crm.membership_multi')
    part_type_selection = fields.Boolean(string='Enable Party Types', config_parameter='fm_sale_crm.part_type_selection')
    mandatory_fields = fields.Boolean(string='Enable Prospect Mandatory Fields', config_parameter='fm_sale_crm.mandatory_fields')
    target_mandatory_fields = fields.Boolean(string='Enable Target Non-Mandatory Fields', config_parameter='fm_sale_crm.target_mandatory_fields')
