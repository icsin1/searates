# -*- coding: utf-8 -*-

from odoo.tests import Form
from odoo import fields, api, SUPERUSER_ID
from odoo.tests.common import TransactionCase, tagged
from odoo.http import request


@tagged('post_install', '-at_install')
class VatReportTZ(TransactionCase):

    @classmethod
    def create_move(cls, date=None, currency=None, post=False, move_type=None, tax_ids=None, price=0):
        move = cls.env['account.move'].with_company(cls.company_data['company']).create({
            'move_type': move_type or 'entry',
            'date': date or '2024-01-01',
            'invoice_date': date or '2024-01-01',
            'partner_id': cls.partner_1.id,
            'currency_id': currency and currency.id or cls.company_data['currency'],
            'invoice_line_ids': [
                (0, None, {
                    'name': 'Vat Report',
                    'account_id': cls.company_data['default_account_revenue'].id,
                    'tax_ids': [(6, 0, tax_ids.ids)],
                    'price_unit': price,
                }),
            ]
        })
        if post:
            move.action_post()
        return move

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        ''' Create a new company having the name passed as parameter.
        A chart of accounts will be installed to this company: the same as the current company one.
        The current user will get access to this company.

        :param chart_template: The chart template to be used on this new company.
        :param company_name: The name of the company.
        :return: A dictionary will be returned containing all relevant accounting data for testing.
        '''

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
            'country_id': cls.env.ref('base.tz').id,
            'currency_id': cls.env.ref('base.TZS').id,
            **kwargs,
        })
        cls.env.user.company_ids |= company

        chart_template.try_loading(company=company, install_demo=False)

        # The currency could be different after the installation of the chart template.
        if kwargs.get('currency_id'):
            company.write({'currency_id': kwargs['currency_id']})
        return {
            'company': company,
            'currency': company.currency_id,
            'default_account_revenue': cls.env['account.account'].search([
                ('company_id', '=', company.id),
                ('user_type_id', '=', cls.env.ref('account.data_account_type_revenue').id)
            ], limit=1),
            'default_account_expense': cls.env['account.account'].search([
                ('company_id', '=', company.id),
                ('user_type_id', '=', cls.env.ref('account.data_account_type_expenses').id)
            ], limit=1),
            'default_account_receivable': search_account(company, chart_template, 'property_account_receivable_id', [
                ('user_type_id.type', '=', 'receivable')
            ]),
            'default_account_payable': cls.env['account.account'].search([
                ('company_id', '=', company.id),
                ('user_type_id.type', '=', 'payable')
            ], limit=1),
            'default_account_assets': cls.env['account.account'].search([
                ('company_id', '=', company.id),
                ('user_type_id', '=', cls.env.ref('account.data_account_type_current_assets').id)
            ], limit=1),
            'default_account_tax_sale': company.account_sale_tax_id.mapped('invoice_repartition_line_ids.account_id'),
            'default_account_tax_purchase': company.account_purchase_tax_id.mapped(
                'invoice_repartition_line_ids.account_id'),
            'default_journal_misc': cls.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('type', '=', 'general')
            ], limit=1),
            'default_journal_sale': cls.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('type', '=', 'sale')
            ], limit=1),
            'default_journal_purchase': cls.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('type', '=', 'purchase')
            ], limit=1),
            'default_journal_bank': cls.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('type', '=', 'bank')
            ], limit=1),
            'default_journal_cash': cls.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('type', '=', 'cash')
            ], limit=1),
            'default_tax_sale': company.account_sale_tax_id,
            'default_tax_purchase': company.account_purchase_tax_id,
        }

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass()

        # Customer related data
        cls.company_data = cls.setup_company_data('Tanzania Comapny',
                                                  chart_template=cls.env.ref('l10n_tz.l10n_tz_chart_template_standard'))
        cls.partner_1 = cls.env['res.partner'].with_company(cls.company_data['company']).create({
            'name': 'Julia Agrolait',
            'email': 'julia@agrolait.example.com',
        })
        CurrencyRate = cls.env['res.currency.rate']

        CurrencyRate.with_company(cls.company_data['company']).create([
            {
                'currency_id': cls.env.ref('base.INR').id,
                'name': '2024-04-15',
                'rate': 5.0,
            }
        ])

    def get_section_values(self, section_line):
        report = self.env.ref('l10n_tz_reports.l10n_tz_tax_web_report')
        section_data = report.with_company(self.company_data['company']).get_web_report({}).get('sections')
        for section in section_data:
            if section.get('title') == section_line:
                return section['values']['main_group']
                self.assertEqual(section['values']['main_group'].get('sale_parent_section_base_original'), 10000.0)
                self.assertEqual(section['values']['main_group'].get('sale_parent_section_vat_original'), 1800.0)

    def test_standard_rated_sales_same_currency_(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_sale_18').name]
        tax_ids = self.env['account.tax'].search(
            [('name', 'in', vat_temps), ('company_id', '=', self.company_data['company'].id)])

        self.create_move(date='2024-04-17', move_type='out_invoice', post=True, tax_ids=tax_ids, price=10000)

        section = self.get_section_values('1. Standard Rated Sales')
        self.assertEqual(section.get('sale_parent_section_base_original'), 10000.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 1800.0)

    def test_standard_rated_sales_diff_currency(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_sale_18').name]
        tax_ids = self.env['account.tax'].search(
            [('name', 'in', vat_temps), ('company_id', '=', self.company_data['company'].id)])

        self.create_move(date='2024-04-17', move_type='out_invoice', post=True, tax_ids=tax_ids, price=10000,
                         currency=self.env.ref('base.INR'))

        section = self.get_section_values('1. Standard Rated Sales')
        self.assertEqual(section.get('sale_parent_section_base_original'), 2000.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 360.0)

    def test_zero_rated_sales_local(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_sale_0_local').name]
        tax_ids = self.env['account.tax'].search(
            [('name', 'in', vat_temps), ('company_id', '=', self.company_data['company'].id)])

        self.create_move(date='2024-04-17', move_type='out_invoice', post=True, tax_ids=tax_ids, price=8000)

        section = self.get_section_values('3. Zero Rated Sales (Local)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 8000.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 0.0)

    def test_zero_rated_sales_export(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_sale_0_export').name]
        tax_ids = self.env['account.tax'].search(
            [('name', 'in', vat_temps), ('company_id', '=', self.company_data['company'].id)])

        self.create_move(date='2024-04-17', move_type='out_invoice', post=True, tax_ids=tax_ids, price=8000)

        section = self.get_section_values('4. Zero Rated Sales - Export (Zero rated Supplies)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 8000.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 0.0)

    def test_exempt_sales_local(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_sale_exempt').name]
        tax_ids = self.env['account.tax'].search(
            [('name', 'in', vat_temps), ('company_id', '=', self.company_data['company'].id)])

        self.create_move(date='2024-04-17', move_type='out_invoice', post=True, tax_ids=tax_ids, price=8000)

        section = self.get_section_values('5. Exempt Sales - Local')
        self.assertEqual(section.get('sale_parent_section_base_original'), 8000.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 0.0)

    def test_total_sales(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_sale_exempt').name,
                     self.env.ref('l10n_tz.tz_tax_sale_0_export').name,
                     self.env.ref('l10n_tz.tz_tax_sale_0_local').name,
                     self.env.ref('l10n_tz.tz_tax_sale_18').name]
        for temp in vat_temps:
            tax_ids = self.env['account.tax'].search(
                [('name', '=', temp), ('company_id', '=', self.company_data['company'].id)])
            self.create_move(date='2024-04-17', move_type='out_invoice', post=True, tax_ids=tax_ids, price=1000)

        section = self.get_section_values('Total (Sum of row 1 to 5)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 4000.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 180.0)

    def test_standard_rated_purchase_local(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_purchase_18_local').name]
        tax_ids = self.env['account.tax'].search(
            [('name', 'in', vat_temps), ('company_id', '=', self.company_data['company'].id)])

        self.create_move(date='2024-04-17', move_type='in_invoice', post=True, tax_ids=tax_ids, price=8500)

        section = self.get_section_values(
            '1. Standard Rated Purchase - Local (Transfer total from Local receipt & GePG receipts)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 8500.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 1530.0)

    def test_standard_rated_purchase_import(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_purchase_18_import').name]
        tax_ids = self.env['account.tax'].search(
            [('name', 'in', vat_temps), ('company_id', '=', self.company_data['company'].id)])

        self.create_move(date='2024-04-17', move_type='in_invoice', post=True, tax_ids=tax_ids, price=8500)

        section = self.get_section_values(
            '2. Standard Rated Purchases - Imports (Transfer total from Wharfage and Imports)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 8500.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 1530.0)

    def test_exempt_purchase_local(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_purchase_exempt_local').name]
        tax_ids = self.env['account.tax'].search(
            [('name', 'in', vat_temps), ('company_id', '=', self.company_data['company'].id)])

        self.create_move(date='2024-04-17', move_type='in_invoice', post=True, tax_ids=tax_ids, price=6501)

        section = self.get_section_values('3. Exempt Purchases - Local')
        self.assertEqual(section.get('sale_parent_section_base_original'), 6501.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 0.0)

    def test_exempt_purchase_import(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_purchase_exempt_import').name]
        tax_ids = self.env['account.tax'].search(
            [('name', 'in', vat_temps), ('company_id', '=', self.company_data['company'].id)])

        self.create_move(date='2024-04-17', move_type='in_invoice', post=True, tax_ids=tax_ids, price=6501)

        section = self.get_section_values('4. Exempt Purchases - Imports')
        self.assertEqual(section.get('sale_parent_section_base_original'), 6501.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 0.0)

    def test_total_purchase(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_purchase_exempt_import').name,
                     self.env.ref('l10n_tz.tz_tax_purchase_exempt_import').name,
                     self.env.ref('l10n_tz.tz_tax_purchase_exempt_local').name,
                     self.env.ref('l10n_tz.tz_tax_purchase_18_import').name,
                     self.env.ref('l10n_tz.tz_tax_purchase_18_local').name,
                     ]
        for temp in vat_temps:
            tax_ids = self.env['account.tax'].search(
                [('name', '=', temp), ('company_id', '=', self.company_data['company'].id)])
            self.create_move(date='2024-04-17', move_type='in_invoice', post=True, tax_ids=tax_ids, price=500)

        section = self.get_section_values('Total (Sum of row 1 to 6)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 2500.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 180.0)

    def test_output_tax_for_period(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_sale_exempt').name,
                     self.env.ref('l10n_tz.tz_tax_sale_0_export').name,
                     self.env.ref('l10n_tz.tz_tax_sale_0_local').name,
                     self.env.ref('l10n_tz.tz_tax_sale_18').name]
        for temp in vat_temps:
            tax_ids = self.env['account.tax'].search(
                [('name', '=', temp), ('company_id', '=', self.company_data['company'].id)])
            self.create_move(date='2024-04-17', move_type='out_invoice', post=True, tax_ids=tax_ids, price=2000)

        section = self.get_section_values('1. Output Tax for the Period (Transfer from Supplies Of Goods and Services)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 0.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 360.0)

    def test_input_tax_for_period(self):
        vat_temps = [self.env.ref('l10n_tz.tz_tax_purchase_exempt_import').name,
                     self.env.ref('l10n_tz.tz_tax_purchase_exempt_import').name,
                     self.env.ref('l10n_tz.tz_tax_purchase_exempt_local').name,
                     self.env.ref('l10n_tz.tz_tax_purchase_18_import').name,
                     self.env.ref('l10n_tz.tz_tax_purchase_18_local').name,
                     ]
        for temp in vat_temps:
            tax_ids = self.env['account.tax'].search(
                [('name', '=', temp), ('company_id', '=', self.company_data['company'].id)])
            self.create_move(date='2024-04-17', move_type='in_invoice', post=True, tax_ids=tax_ids, price=500)

        section = self.get_section_values('2. Input Tax for the period (Transfer from Purchases Of Goods and Services)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 0.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 180.0)

    def test_total_val_payable_refundable(self):
        purchase_vat_temps = [self.env.ref('l10n_tz.tz_tax_purchase_exempt_import').name,
                              self.env.ref('l10n_tz.tz_tax_purchase_exempt_import').name,
                              self.env.ref('l10n_tz.tz_tax_purchase_exempt_local').name,
                              self.env.ref('l10n_tz.tz_tax_purchase_18_import').name,
                              self.env.ref('l10n_tz.tz_tax_purchase_18_local').name,
                              ]
        for temp in purchase_vat_temps:
            tax_ids = self.env['account.tax'].search(
                [('name', '=', temp), ('company_id', '=', self.company_data['company'].id)])
            self.create_move(date='2024-04-17', move_type='in_invoice', post=True, tax_ids=tax_ids, price=500)

        sale_vat_temps = [self.env.ref('l10n_tz.tz_tax_sale_exempt').name,
                          self.env.ref('l10n_tz.tz_tax_sale_0_export').name,
                          self.env.ref('l10n_tz.tz_tax_sale_0_local').name,
                          self.env.ref('l10n_tz.tz_tax_sale_18').name]
        for temp in sale_vat_temps:
            tax_ids = self.env['account.tax'].search(
                [('name', '=', temp), ('company_id', '=', self.company_data['company'].id)])
            self.create_move(date='2024-04-17', move_type='out_invoice', post=True, tax_ids=tax_ids, price=2000)

        section = self.get_section_values('3. Total VAT Payable/(Refundable)  - (Row 1 minus 2)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 0.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 180.0)

        section = self.get_section_values('Total VAT Due/(Carried Forward) - (row 3 minus 4)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 0.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), 180.0)

    def test_total_val_payable_refundable_02(self):
        purchase_vat_temps = [self.env.ref('l10n_tz.tz_tax_purchase_exempt_import').name,
                              self.env.ref('l10n_tz.tz_tax_purchase_exempt_import').name,
                              self.env.ref('l10n_tz.tz_tax_purchase_exempt_local').name,
                              self.env.ref('l10n_tz.tz_tax_purchase_18_import').name,
                              self.env.ref('l10n_tz.tz_tax_purchase_18_local').name,
                              ]
        for temp in purchase_vat_temps:
            tax_ids = self.env['account.tax'].search(
                [('name', '=', temp), ('company_id', '=', self.company_data['company'].id)])
            self.create_move(date='2024-04-17', move_type='in_invoice', post=True, tax_ids=tax_ids, price=2000)

        sale_vat_temps = [self.env.ref('l10n_tz.tz_tax_sale_exempt').name,
                          self.env.ref('l10n_tz.tz_tax_sale_0_export').name,
                          self.env.ref('l10n_tz.tz_tax_sale_0_local').name,
                          self.env.ref('l10n_tz.tz_tax_sale_18').name]
        for temp in sale_vat_temps:
            tax_ids = self.env['account.tax'].search(
                [('name', '=', temp), ('company_id', '=', self.company_data['company'].id)])
            self.create_move(date='2024-04-17', move_type='out_invoice', post=True, tax_ids=tax_ids, price=500)

        section = self.get_section_values('3. Total VAT Payable/(Refundable)  - (Row 1 minus 2)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 0.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), -630.0)

        section = self.get_section_values('Total VAT Due/(Carried Forward) - (row 3 minus 4)')
        self.assertEqual(section.get('sale_parent_section_base_original'), 0.0)
        self.assertEqual(section.get('sale_parent_section_vat_original'), -630.0)
