from odoo import models, fields


class AccountTaxReportLine(models.Model):
    _inherit = 'account.tax.report.line'

    include_additional_data_domain = fields.Boolean(default=False)
    additional_data_domain = fields.Text(string='Include Lines Domain', help='Check for records and include in the result')
