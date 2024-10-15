# -*- coding: utf-8 -*-

from . import models
from odoo import api, SUPERUSER_ID


def l10n_in_tds_tcs_post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    chart_template_id = env.ref('l10n_in.indian_chart_template_standard')
    tax_template_ids = env['account.tax.template'].search([('chart_template_id', '=', chart_template_id.id)])
    account_template_ids = env['account.account.template'].search([('chart_template_id', '=', chart_template_id.id)])
    company_ids = env['res.company'].search([('partner_id.country_id.code', '=', 'IN')])

    for company in company_ids:
        taxes_ref = {}
        account_ref = {}
        acc_xml_ids = account_template_ids.get_external_id()
        for acc_template in account_template_ids:
            module, xml_id = acc_xml_ids.get(acc_template.id).split('.')
            account_id = env.ref('%s.%s_%s' % (module, company.id, xml_id), raise_if_not_found=False)
            if not account_id:
                account_template_ref = chart_template_id.generate_account(taxes_ref, account_ref, chart_template_id.code_digits, company)
                account_ref.update(account_template_ref)

        tax_xml_ids = tax_template_ids.get_external_id()
        for tax_template in tax_template_ids:
            module, xml_id = tax_xml_ids.get(tax_template.id).split('.')
            tax = env.ref('%s.%s_%s' % (module, company.id, xml_id), raise_if_not_found=False)
            if not tax:
                tax_templates = tax_template.children_tax_ids | tax_template
                generated_tax_res = tax_templates._generate_tax(company)
                for repartition_line, value in generated_tax_res['account_dict']['account.tax.repartition.line'].items():
                    if value.get('account_id') and account_ref.get(value['account_id']):
                        repartition_line.account_id = account_ref.get(value['account_id']).id
