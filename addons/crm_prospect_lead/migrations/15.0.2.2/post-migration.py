# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    leads = env['crm.prospect.lead'].search([])
    for lead in leads:
        if lead.lead_source:
            if lead.lead_source == 'db':
                lead.lead_source_id = env.ref('crm_prospect_lead.crm_lead_source_database').id
            if lead.lead_source == 'social':
                lead.lead_source_id = env.ref('crm_prospect_lead.crm_lead_source_social').id
            if lead.lead_source == 'customer_ref':
                lead.lead_source_id = env.ref('crm_prospect_lead.crm_lead_source_customer_reference').id
            if lead.lead_source == 'trade_show':
                lead.lead_source_id = env.ref('crm_prospect_lead.crm_lead_trade_show').id
            if lead.lead_source == 'inbound':
                lead.lead_source_id = env.ref('crm_prospect_lead.crm_lead_source_inbound').id
