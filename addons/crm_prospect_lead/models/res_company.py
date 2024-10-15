# -*- coding: utf-8 -*-

from odoo import models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _create_per_company_freight_sequence(self):
        super()._create_per_company_freight_sequence()
        freight_sequence_obj = self.env['freight.sequence']
        val_lst = []
        lead_company_sequence = self.env.ref('crm_prospect_lead.crm_prospect_lead_seq')
        if lead_company_sequence.company_id != self:
            lead_company_sequence = lead_company_sequence.copy({'company_id': self.id})
        lead_vals = {
            'name': 'Prospect Lead',
            'ir_model_id': self.env.ref('crm_prospect_lead.model_crm_prospect_lead').id,
            'ir_field_id': self.env.ref('crm_prospect_lead.field_crm_prospect_lead__name').id,
            'ir_sequence_id': lead_company_sequence.id,
            'sequence_format': 'LE',
            'number_increment': 1,
            'padding': 5,
            'company_id': self.id
        }
        val_lst.append(lead_vals)
        opportunity_company_sequence = self.env.ref('crm_prospect_lead.crm_prospect_opportunity_seq')
        if opportunity_company_sequence.company_id != self:
            opportunity_company_sequence = opportunity_company_sequence.copy({'company_id': self.id})
        opportunity_vals = {
            'name': 'Prospect Opportunity',
            'ir_model_id': self.env.ref('crm_prospect_lead.model_crm_prospect_opportunity').id,
            'ir_field_id': self.env.ref('crm_prospect_lead.field_crm_prospect_opportunity__name').id,
            'ir_sequence_id': opportunity_company_sequence.id,
            'sequence_format': 'OP',
            'number_increment': 1,
            'padding': 5,
            'company_id': self.id
        }
        val_lst.append(opportunity_vals)
        if val_lst:
            freight_sequence_obj.create(val_lst)
