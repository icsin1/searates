# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WizardLeadStatus(models.TransientModel):
    _name = "wizard.prospect.lead.status"
    _description = "Wizard Prospect Lead Status"
    _rec_name = 'stage_id'

    prospect_lead_id = fields.Many2one('crm.prospect.lead', required=True)
    stage_id = fields.Many2one('crm.prospect.lead.stage', string="Lead Stage", required=True)
    remarks = fields.Text()
    lead_category = fields.Selection([
        ('hot', 'HOT'),
        ('warm', 'WARM'),
        ('cold', 'COLD')
    ])
    show_lead_category = fields.Boolean(compute='cal_show_lead_category')

    @api.depends('stage_id')
    def cal_show_lead_category(self):
        future_prospect_stage_id = self.env.ref('crm_prospect_lead.crm_lead_stage_future_prospect')
        for rec in self:
            show_lead_category = False
            if rec.stage_id.id == future_prospect_stage_id.id:
                show_lead_category = True
            rec.show_lead_category = show_lead_category

    def action_change_status(self):
        vals = {'stage_id': self.stage_id.id}
        if self.lead_category:
            vals['lead_category'] = self.lead_category
        if self.remarks:
            vals['remarks'] = self.remarks
        self.prospect_lead_id.write(vals)
