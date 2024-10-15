# -*- coding: utf-8 -*-

from . import models
from . import wizard

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def _auto_create_pdc_account(env, company):
    _logger.info("Creating PDC Accounts for {}".format(company.name))
    AccountJournal = env['account.journal'].sudo()
    Account = env['account.account'].sudo()
    pdc_receivable_account_id = AccountJournal._get_pdc_receivable_account(company)
    if not pdc_receivable_account_id:
        code = env['pdc.payment']._get_pdc_receivable_code(company)
        default_account_vals = AccountJournal._prepare_pdc_account_vals(company, 'PDC Receivable', code)
        pdc_receivable_account_id = Account.create(default_account_vals).id
    company.pdc_receivable_account_id = pdc_receivable_account_id
    pdc_payable_account_id = AccountJournal._get_pdc_payable_account(company)
    if not pdc_payable_account_id:
        code = env['pdc.payment']._get_pdc_payable_code(company)
        default_account_vals = AccountJournal._prepare_pdc_account_vals(company, 'PDC Payable', code)
        pdc_payable_account_id = Account.create(default_account_vals).id
    company.pdc_payable_account_id = pdc_payable_account_id


def _ics_account_pdc_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for company in env['res.company'].search([('chart_template_id', '!=', False)]):
        _auto_create_pdc_account(env, company)
