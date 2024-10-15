from odoo import api, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def _prepare_pdc_account_vals(self, company, name, code):
        return {
            'name': name,
            'code': code,
            'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
            'company_id': company.id,
            'reconcile': True,
        }

    @api.model
    def _get_pdc_receivable_account(self, company_id):
        code = self.env['pdc.payment']._get_pdc_receivable_code(company_id)
        return self.env['account.account'].search(
            [('code', '=', code), ('company_id', '=', company_id.id)], limit=1)

    @api.model
    def _get_pdc_payable_account(self, company_id):
        code = self.env['pdc.payment']._get_pdc_payable_code(company_id)
        return self.env['account.account'].search(
            [('code', '=', code), ('company_id', '=', company_id.id)], limit=1)

    @api.model
    def _fill_missing_values(self, vals):
        res = super()._fill_missing_values(vals)
        journal_type = vals.get('type')
        if journal_type and journal_type == "bank":
            company = self.env['res.company'].browse(vals['company_id']) if vals.get('company_id') else self.env.company
            pdc_receivable_account_id = self._get_pdc_receivable_account(company)
            if not pdc_receivable_account_id:
                code = self.env['pdc.payment']._get_pdc_receivable_code(company)
                default_account_vals = self._prepare_pdc_account_vals(company, 'PDC Receivable', code)
                company.pdc_receivable_account_id = self.env['account.account'].create(default_account_vals).id
            pdc_payable_account_id = self._get_pdc_payable_account(company)
            if not pdc_payable_account_id:
                code = self.env['pdc.payment']._get_pdc_payable_code(company)
                default_account_vals = self._prepare_pdc_account_vals(company, 'PDC Payable', code)
                company.pdc_payable_account_id = self.env['account.account'].create(default_account_vals).id
        return res
