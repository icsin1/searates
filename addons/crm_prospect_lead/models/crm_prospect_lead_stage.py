# -*- coding: utf-8 -*-

from odoo import models, fields


class ProspectLeadStage(models.Model):
    _name = "crm.prospect.lead.stage"
    _description = "Lead Stage"
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=99)
    is_create_opportunity = fields.Boolean(string="Create Opportunity")
