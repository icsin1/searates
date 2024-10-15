# -*- coding: utf-8 -*-

from odoo import models, fields


class CrmProspect(models.Model):
    _inherit = "crm.prospect"

    lead_count = fields.Integer(compute='cal_prospect_lead')
    prospect_lead_ids = fields.One2many('crm.prospect.lead', 'prospect_id', string='Leads')

    def cal_prospect_lead(self):
        for rec in self:
            rec.lead_count = len(rec.prospect_lead_ids)

    def action_create_lead(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm_prospect_lead.crm_prospect_lead_action_new")
        action['context'] = {
            'default_prospect_id': self.id,
            'default_company_id': self.company_id.id,
            'default_street1': self.street1,
            'default_country_id': self.country_id.id,
            'default_state_id': self.state_id.id,
            'default_city_id': self.city_id.id,
            'default_zip': self.zip,
            'default_mobile': self.mobile,
            'default_phone_no': self.phone_no,
        }
        return action

    def action_open_prospect_lead(self):
        self.ensure_one()
        context = self._context.copy()
        context.update(
            default_prospect_id=self.id,
            default_company_id=self.company_id.id,
        )
        action = self.env['ir.actions.act_window']._for_xml_id('crm_prospect_lead.crm_prospect_lead_action')
        prospect_lead_ids = self.prospect_lead_ids
        if len(prospect_lead_ids) == 1:
            res = self.env.ref('crm_prospect_lead.crm_prospect_lead_view_form', False)
            form_view = [(res and res.id or False, 'form')]
            action.update({
                'view_mode': 'form',
                'views': form_view,
                'res_id': prospect_lead_ids.id,
                'context': context,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', prospect_lead_ids.ids)],
                'context': context,
            })
        return action
