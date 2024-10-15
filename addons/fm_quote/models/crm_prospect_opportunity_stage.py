# -*- coding: utf-8 -*-

from odoo import models, fields


class ProspectOpportunityStage(models.Model):
    _inherit = "crm.prospect.opportunity.stage"

    allow_quote_creation = fields.Boolean(default=True)
