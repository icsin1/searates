from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def js_report_data(self, report_type, domain=[], **kwargs):

        # Forcing active company only
        domain = domain + [('company_id', '=', self.env.company.id)]

        report_method = '_get_{}_report_data'.format(report_type)
        if hasattr(self, report_method):
            return getattr(self, report_method)(domain, **kwargs)

        raise UserError(_('Invalid report type: {}'.format(report_type)))

    def _format_currency(self, amount, currency=None):
        return formatLang(self.env, amount, currency_obj=currency or self.env.company.currency_id)
