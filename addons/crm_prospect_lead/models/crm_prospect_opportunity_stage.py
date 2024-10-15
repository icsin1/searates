# -*- coding: utf-8 -*-

from odoo import models, fields


class ProspectOpportunityStage(models.Model):
    _name = "crm.prospect.opportunity.stage"
    _description = "Opportunity Stage"
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=99)
