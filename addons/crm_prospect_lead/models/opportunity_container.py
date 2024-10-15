# -*- coding: utf-8 -*-

from odoo import models, fields


class OpportunityContainer(models.Model):
    _name = "crm.prospect.opportunity.container"
    _description = "Opportunity Container"

    opportunity_id = fields.Many2one("crm.prospect.opportunity", string="Linked Opportunity", required=True, ondelete='cascade')
    container_type_id = fields.Many2one("freight.container.type", string="Container Type", required=True)
    quantity = fields.Integer("Container Quantity", default=1, required=True)
