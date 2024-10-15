# -*- coding: utf-8 -*-

import time
from datetime import datetime, date
from odoo.tests import Form
from odoo.tests.common import TransactionCase, tagged


CURRENT_DATE = '2023-12-01'


@tagged('post_install', '-at_install')
class ICSAccountDeferredCommon(TransactionCase):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super(ICSAccountDeferredCommon, cls).setUpClass()

        if chart_template_ref:
            chart_template = cls.env.ref(chart_template_ref)
        else:
            chart_template = cls.env.ref('l10n_generic_coa.configurable_chart_template', raise_if_not_found=False)
        if not chart_template:
            cls.tearDownClass()
            # skipTest raises exception
            cls.skipTest(cls, "Accounting Tests skipped because the user's company has no chart of accounts.")

        # Create user.
        user = cls.env['res.users'].create({
            'name': 'Harry Winks!',
            'login': 'accountman',
            'password': 'accountman',
            'groups_id': [(6, 0, cls.env.user.groups_id.ids), (4, cls.env.ref('account.group_account_user').id)],
        })
        user.partner_id.email = 'accountman@test.com'

        # Shadow the current environment/cursor with one having the report user.
        # This is mandatory to test access rights.
        cls.env = cls.env(user=user)
        cls.cr = cls.env.cr

        cls.company_data = cls.setup_company_data('company_data', chart_template=chart_template)

        user.write({
            'company_id': cls.company_data['company'].id,
        })
        # ==== Partners ====
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'partner_a',
            'property_account_receivable_id': cls.company_data['default_account_receivable'].id,
            'property_account_payable_id': cls.company_data['default_account_payable'].id,
            'company_id': False,
        })

        # Setup Account Data
        cls.revenue_account_id = cls.env['account.account'].search([
            ('company_id', '=', cls.company_data['company'].id),
            ('user_type_id', '=', cls.env.ref('account.data_account_type_revenue').id)
        ], limit=1)
        cls.deferred_revenue_account_id = cls.env['account.account'].search([
            ('company_id', '=', cls.company_data['company'].id),
            ('user_type_id', '=', cls.env.ref('account.data_account_type_current_liabilities').id)
        ], limit=1)
        cls.deferred_account_expense_id = cls.env['account.account'].search([
            ('company_id', '=', cls.company_data['company'].id),
            ('user_type_id', '=', cls.env.ref('account.data_account_type_expenses').id)
        ], limit=1)
        cls.expense_account_id = cls.env['account.account'].search([
            ('company_id', '=', cls.company_data['company'].id),
            ('user_type_id', '=', cls.env.ref('account.data_account_type_prepayments').id)
        ], limit=1)

        # Setup Account Journal Data
        cls.journal_id = cls.env['account.journal'].search([
            ('company_id', '=', cls.company_data['company'].id),
            ('type', '=', 'general')
        ], limit=1)

        # Fiscal Year
        cls.setup_fiscal_year()

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        """ Create a new company having the name passed as parameter.
        A chart of accounts will be installed to this company: the same as the current company one.
        The current user will get access to this company.

        :param chart_template: The chart template to be used on this new company.
        :param company_name: The name of the company.
        :return: A dictionary will be returned containing all relevant accounting data for testing.
        """
        def search_account(company, chart_template, field_name, domain):
            template_code = chart_template[field_name].code
            domain = [('company_id', '=', company.id)] + domain

            account = None
            if template_code:
                account = cls.env['account.account'].search(domain + [('code', '=like', template_code + '%')], limit=1)

            if not account:
                account = cls.env['account.account'].search(domain, limit=1)
            return account

        chart_template = chart_template or cls.env.company.chart_template_id
        company = cls.env['res.company'].create({
            'name': company_name,
            **kwargs,
        })

        chart_template.try_loading(company=company, install_demo=False)

        # The currency could be different after the installation of the chart template.
        if kwargs.get('currency_id'):
            company.write({'currency_id': kwargs['currency_id']})

        return {
            'company': company,
            'currency': company.currency_id,
            'default_account_receivable': search_account(company, chart_template, 'property_account_receivable_id', [
                ('user_type_id.type', '=', 'receivable')
            ]),
            'default_account_payable': cls.env['account.account'].search([
                ('company_id', '=', company.id),
                ('user_type_id.type', '=', 'payable')
            ], limit=1),
        }

    @classmethod
    def create_account_asset(cls, name, depreciation_id, depreciation_expense_id, journal_id, asset_type, **kw):
        """
        Create record of Asset based on asset_type.

        @param {string} name: name
        @param {recordset} depreciation_id: record of 'account.account'
        @param {recordset} depreciation_expense_id: record of 'account.account'
        @param {recordset} journal_id: record of 'account.journal'
        @param {recordset} asset_type: asset_type ['model','sale', 'expense']
        @return {recordset}: single record of 'account.asset'
        """
        test_context = dict(
            _test_current_date=datetime.strptime(CURRENT_DATE, '%Y-%m-%d').date() if kw.get('current_date') else date.today()
        )
        asset_form = Form(cls.env["account.asset"].with_context({
            'default_asset_type': asset_type,
            'default_state': kw.get('state') if kw.get('state') else 'draft',
            **(test_context if kw.get('first_recognition_date') or kw.get('current_date') else {})
        }))
        asset_form.name = name
        asset_form.account_depreciation_id = depreciation_id
        asset_form.account_depreciation_expense_id = depreciation_expense_id
        asset_form.journal_id = journal_id

        if kw.get('original_value'):
            asset_form.original_value = kw.get('original_value')
        if kw.get('interval_period'):
            asset_form.interval_period = kw.get('interval_period')
        if kw.get('interval'):
            asset_form.recognition_interval = kw.get('interval')
        if kw.get('first_recognition_date'):
            asset_form.first_recognition_date = kw.get('first_recognition_date')
        if kw.get('prorata'):
            asset_form.prorata = kw.get('prorata')
        if kw.get('prorata_date'):
            asset_form.prorata_date = kw.get('prorata_date')
        if kw.get('acquisition_date'):
            asset_form.acquisition_date = kw.get('acquisition_date')
        return asset_form.save()

    @classmethod
    def create_product(cls, name, uom_id, **kwargs):
        """
        Create Product
        @param {string} name: name of product
        @param {recordset} uom_id: record of uom.uom
        @returns {recordset}: record of 'product.product'
        """
        product_form = Form(cls.env['product.product'])
        product_form.name = name
        product_form.uom_id = uom_id
        return product_form.save()

    def create_invoice(self, move_type='out_invoice', invoice_amount=None, partner_id=None, currency_id=None, date_invoice=None, auto_validate=False, coa_id=False):
        date_invoice = date_invoice or time.strftime('%Y') + '-07-01'

        invoice_vals = {
            'move_type': move_type,
            'partner_id': partner_id or self.partner_a,
            'invoice_date': date_invoice,
            'date': date_invoice,
            'invoice_line_ids': [(0, 0, {
                'name': 'product that cost %s' % invoice_amount,
                'account_id': coa_id,
                'quantity': 1,
                'price_unit': invoice_amount,
                'tax_ids': [(6, 0, [])],
            })]
        }

        if currency_id:
            invoice_vals['currency_id'] = currency_id

        invoice = self.env['account.move'].with_context(default_move_type=move_type).create(invoice_vals)
        if auto_validate:
            invoice.action_post()
        return invoice

    @classmethod
    def setup_fiscal_year(cls):
        cls.company_data['company'].fiscalyear_last_day = 31
        cls.company_data['company'].fiscalyear_last_month = "3"

        # Create custom fiscal year covering the 6 first months of 2017.
        current_year = datetime.strptime(CURRENT_DATE, '%Y-%m-%d').date().strftime("%Y")
        cls.env["account.fiscal.year"].create(
            {
                "name": "FY %s-%s" % (current_year, int(current_year)+1),
                "date_from": "%s-04-01" % current_year,
                "date_to": "%s-03-31" % (int(current_year)+1),
                "company_id": cls.company_data['company'].id,
            }
        )

    @classmethod
    def get_fiscal_year(cls):
        fiscalyear_dates = cls.env.company.compute_fiscalyear_dates(datetime.strptime(CURRENT_DATE, '%Y-%m-%d').date())
        return fiscalyear_dates
