# -*- coding: utf-8 -*-

from odoo import models, fields, _


class WizardLeadStatus(models.TransientModel):
    _name = "wizard.prospect.opportunity.status"
    _description = "Wizard Prospect Opportunity Status"
    _rec_name = 'stage_id'

    prospect_opportunity_id = fields.Many2one('crm.prospect.opportunity', required=True)
    stage_id = fields.Many2one('crm.prospect.opportunity.stage', string="Opportunity Stage", 
                               required=True)

    def action_change_status(self):
        self.ensure_one()
        vals = {'stage_id': self.stage_id.id}
        self.prospect_opportunity_id.write(vals)
        partner_ids = []
        if self.stage_id.id == self.env.ref('crm_prospect_lead.crm_opportunity_stage_active').id:
            partner_ids = self.prospect_opportunity_id.pricing_team_id.partner_id.ids
            return self.action_send_by_email(partner_ids)
        elif self.stage_id.id == self.env.ref('crm_prospect_lead.crm_opportunity_stage_created').id:
            partner_ids = self.prospect_opportunity_id.user_id.partner_id.ids
            return self.action_send_by_email(partner_ids)

    def action_send_by_email(self, partner_ids):
        template_id = self.env['ir.model.data'].sudo()._xmlid_to_res_id(
            'crm_prospect_lead.opportunity_default_email_template',
            raise_if_not_found=False)
        compose_ctx = dict(
            default_model=self.prospect_opportunity_id._name,
            default_res_id=self.prospect_opportunity_id.id,
            default_use_template=bool(template_id),
            default_subject=self.prospect_opportunity_id.name,
            default_template_id=template_id,
            default_composition_mode='comment',
            default_partner_ids=partner_ids,
            mail_tz=self.env.user.tz,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Opportunity : Mail Composer'),
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': compose_ctx,
        }
