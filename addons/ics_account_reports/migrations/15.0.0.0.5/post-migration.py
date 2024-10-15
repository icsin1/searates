# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Set custom handler in Partner Ledger Report
    web_report = env.ref('ics_account_reports.ics_account_partner_ledger').id
    handler_model = env.ref('ics_account_reports.model_partner_ledger_report_handler')
    query = "UPDATE web_report SET report_handler_model_id = %s, report_handler_model_name = '%s' WHERE id = %s" % (handler_model.id, handler_model.model, web_report)
    cr.execute(query)
