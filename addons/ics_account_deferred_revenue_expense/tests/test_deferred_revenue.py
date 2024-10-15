# -*- coding: utf-8 -*-

import logging
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.ics_account_deferred_revenue_expense.tests.common import ICSAccountDeferredCommon, CURRENT_DATE

_logger = logging.getLogger(__name__)
DATETIME_FORMAT = '%m/%d/%Y'


class TestDeferredRevenue(ICSAccountDeferredCommon):

    def setUp(self):
        super().setUp()
        self.company = self.company_data.get('company')

        # Setup Char of Account Data
        self.setup_char_of_account_data()

        # Setup product data
        self.categ_kgm = self.env.ref('uom.product_uom_categ_kgm')
        self.uom_kg = self.env['uom.uom'].search([('category_id', '=', self.categ_kgm.id), ('uom_type', '=', 'reference')],
                                                 limit=1)
        self.product_1_id = self.create_product('Test Product 1', self.uom_kg)

    def setup_char_of_account_data(self):
        """
        Create Char of Account "Current Liabilities" type record
        """
        self.sale_coa_id = self.env['account.account'].create({
            'code': 100501,
            'name': "Test Deferred Revenue Account",
            'user_type_id': self.env.ref('account.data_account_type_current_liabilities').id
        })

    def test_residual_amount_without_post_entry(self):
        """
        Test case for check "Residual Amount to Recognize" based on the "Original Value".

        In this case,
        Record is in "Draft" state(Without any journal entry)
        Original Value = 7000
        """
        _logger.info("\n\n=================== Started Residual Amount Without post any Journal Entries ===================\n")

        revenue_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale', original_value=7000,
                                               current_date=CURRENT_DATE)

        self.assertEqual(revenue_id.residual_amount, 7000)
        self.assertEqual(revenue_id.company_id.id, self.company_data['company'].id)
        self.assertEqual(revenue_id.recognition_interval, 1)
        self.assertEqual(revenue_id.interval_period, 'years')
        self.assertEqual(revenue_id.acquisition_date.strftime(DEFAULT_SERVER_DATE_FORMAT), date.today().strftime(DEFAULT_SERVER_DATE_FORMAT))
        self.assertEqual(revenue_id.first_recognition_date, self.get_fiscal_year().get('date_to'))

        _logger.info("\n\n=================== Completed Residual Amount Without post any Journal Entries ===================\n")

    def test_residual_amount_with_post_entry(self):
        """
        Test case for check "Residual Amount to Recognize" based on the "Original Value" after 1st journal entry posted.

        In this case,
        Interval should be 6 months and validated record after validating post 1st journal entry.
        Prorata = False
        Interval Period = 6 Months
        First Recognition Date = 31/12/2023
        """
        _logger.info("\n\n=================== Started Residual Amount With post any Journal Entries ===================\n")

        revenue_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale', original_value=7000,
                                               interval_period='months', interval=6, first_recognition_date='2023-12-31', current_date='2023-12-01')

        self.assertEqual(revenue_id.state, "draft")
        self.assertFalse(revenue_id.depreciation_move_ids)

        # Validate Revenue
        revenue_id.button_confirm()

        self.assertEqual(revenue_id.state, "running")
        self.assertTrue(revenue_id.depreciation_move_ids)
        self.assertEqual(len(revenue_id.depreciation_move_ids.ids), 6)
        self.assertNotIn('"posted"', revenue_id.depreciation_move_ids.mapped('state'))

        # Journal Entries Accounting Date
        self.assertEqual(revenue_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '12/31/2023')
        self.assertEqual(revenue_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '01/31/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '02/29/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '04/30/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '05/31/2024')

        # Revenue Charges per month (To be pay monthly)
        self.assertEqual(revenue_id.depreciation_move_ids[0].amount_total, 1166.67)
        self.assertEqual(revenue_id.depreciation_move_ids[1].amount_total, 1166.67)
        self.assertEqual(revenue_id.depreciation_move_ids[2].amount_total, 1166.67)
        self.assertEqual(revenue_id.depreciation_move_ids[3].amount_total, 1166.67)
        self.assertEqual(revenue_id.depreciation_move_ids[4].amount_total, 1166.67)
        self.assertEqual(revenue_id.depreciation_move_ids[5].amount_total, 1166.65)

        # Cumulative Revenue Amount (Total Paid Amount)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_deprecated_value, 1166.67)
        self.assertEqual(revenue_id.depreciation_move_ids[1].asset_deprecated_value, 2333.34)
        self.assertEqual(revenue_id.depreciation_move_ids[2].asset_deprecated_value, 3500.01)
        self.assertEqual(revenue_id.depreciation_move_ids[3].asset_deprecated_value, 4666.68)
        self.assertEqual(revenue_id.depreciation_move_ids[4].asset_deprecated_value, 5833.35)
        self.assertEqual(revenue_id.depreciation_move_ids[5].asset_deprecated_value, 7000.00)

        # Next Period Revenue (Remaining Amount to pay)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_remaining_value, 5833.33)
        self.assertEqual(revenue_id.depreciation_move_ids[1].asset_remaining_value, 4666.66)
        self.assertEqual(revenue_id.depreciation_move_ids[2].asset_remaining_value, 3499.99)
        self.assertEqual(revenue_id.depreciation_move_ids[3].asset_remaining_value, 2333.32)
        self.assertEqual(revenue_id.depreciation_move_ids[4].asset_remaining_value, 1166.65)
        self.assertEqual(revenue_id.depreciation_move_ids[5].asset_remaining_value, 0.00)

        revenue_id.depreciation_move_ids[0].write({'auto_post': False})
        revenue_id.depreciation_move_ids[0].action_post()
        self.assertEqual(revenue_id.residual_amount, 5833.33)

        _logger.info("\n\n=================== Completed Residual Amount With post any Journal Entries ===================\n")

    def test_validate_depreciation_revenue_with_prorata_five_months(self):
        """
        Test case for check Journal Entry's Total amount and dates for the entries by selecting Prorata Date.

        In this case,
        Interval Period = 5 Months
        Original Value = 1,22,780.56
        Prorata = True
        Prorata Date = 02/01/2024
        First Recognition Date = 15/01/2024
        """
        _logger.info("\n\n=================== Started Validate Revenue to generate depreciation amount with Prorata 5 Months ===================\n")

        revenue_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale', original_value=122780.56,
                                               interval_period='months', interval=5, first_recognition_date='2024-01-15', prorata=True, prorata_date='2023-12-15', current_date=CURRENT_DATE)

        self.assertEqual(revenue_id.state, "draft")
        self.assertFalse(revenue_id.depreciation_move_ids)

        # Compute Revenue
        revenue_id.button_compute_depreciation_board()

        self.assertEqual(revenue_id.state, "draft")
        self.assertTrue(revenue_id.depreciation_move_ids)
        self.assertEqual(len(revenue_id.depreciation_move_ids.ids), 6)
        self.assertNotIn('"posted"', revenue_id.depreciation_move_ids.mapped('state'))

        # Journal Entries Accounting Date
        self.assertEqual(revenue_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '01/15/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '02/29/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '04/30/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '05/31/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '06/30/2024')

        # Revenue Charges per month (To be pay monthly)
        self.assertEqual(revenue_id.depreciation_move_ids[0].amount_total, 13466.25)
        self.assertEqual(revenue_id.depreciation_move_ids[1].amount_total, 24556.11)
        self.assertEqual(revenue_id.depreciation_move_ids[2].amount_total, 24556.11)
        self.assertEqual(revenue_id.depreciation_move_ids[3].amount_total, 24556.11)
        self.assertEqual(revenue_id.depreciation_move_ids[4].amount_total, 24556.11)
        self.assertEqual(revenue_id.depreciation_move_ids[5].amount_total, 11089.87)

        # Cumulative Revenue Amount (Total Paid Amount)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_deprecated_value, 13466.25)
        self.assertEqual(revenue_id.depreciation_move_ids[1].asset_deprecated_value, 38022.36)
        self.assertEqual(revenue_id.depreciation_move_ids[2].asset_deprecated_value, 62578.47)
        self.assertEqual(revenue_id.depreciation_move_ids[3].asset_deprecated_value, 87134.58)
        self.assertEqual(revenue_id.depreciation_move_ids[4].asset_deprecated_value, 111690.69)
        self.assertEqual(revenue_id.depreciation_move_ids[5].asset_deprecated_value, 122780.56)

        # Next Period Revenue (Remaining Amount to pay)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_remaining_value, 109314.31)
        self.assertEqual(revenue_id.depreciation_move_ids[1].asset_remaining_value, 84758.2)
        self.assertEqual(revenue_id.depreciation_move_ids[2].asset_remaining_value, 60202.09)
        self.assertEqual(revenue_id.depreciation_move_ids[3].asset_remaining_value, 35645.98)
        self.assertEqual(revenue_id.depreciation_move_ids[4].asset_remaining_value, 11089.87)
        self.assertEqual(revenue_id.depreciation_move_ids[5].asset_remaining_value, 0.00)

        _logger.info("\n\n=================== Completed Validate Revenue to generate depreciation amount with Prorata 5 Months ===================\n")

    def test_validate_depreciation_revenue_with_one_year(self):
        """
        Test case for check Journal Entry's Total amount and dates for the entries.

        In this case,
        Interval Period = 1 Year
        First Recognition Date = 31/12/2023
        Original Value = 7000
        """
        _logger.info("\n\n=================== Started Validate Revenue to generate depreciation amount with 1 year ===================\n")

        revenue_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale', original_value=7000,
                                               interval_period='years', interval=1, first_recognition_date='2023-12-31', current_date='2023-12-01')

        self.assertEqual(revenue_id.state, "draft")
        self.assertFalse(revenue_id.depreciation_move_ids)

        # Validate Revenue
        revenue_id.button_confirm()

        self.assertEqual(revenue_id.state, "running")
        self.assertTrue(revenue_id.depreciation_move_ids)
        self.assertEqual(len(revenue_id.depreciation_move_ids.ids), 1)
        self.assertNotIn('"posted"', revenue_id.depreciation_move_ids.mapped('state'))

        # Journal Entries Accounting Date
        self.assertEqual(revenue_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '12/31/2023')

        # Revenue Charges per month (To be pay monthly)
        self.assertEqual(revenue_id.depreciation_move_ids[0].amount_total, 7000.00)

        # Cumulative Revenue Amount (Total Paid Amount)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_deprecated_value, 7000.00)

        # Next Period Revenue (Remaining Amount to pay)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_remaining_value, 0.00)

        _logger.info("\n\n=================== Completed Validate Revenue to generate depreciation amount with 1 year ===================\n")

    def test_validate_depreciation_revenue_with_five_year(self):
        """
        Test case for check Journal Entry's Total amount and dates for the entries.

        In this case,
        Interval Period = 5 Years
        First Recognition Date = 31/12/2023
        Original Value = 1,25,252.32
        """
        _logger.info("\n\n=================== Started Validate Revenue to generate depreciation amount with 5 year ===================\n")

        revenue_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale', original_value=125252.32,
                                               interval_period='years', interval=5, first_recognition_date='2023-12-31')

        self.assertEqual(revenue_id.state, "draft")
        self.assertFalse(revenue_id.depreciation_move_ids)

        # Validate Revenue
        revenue_id.button_confirm()

        self.assertEqual(revenue_id.state, "running")
        self.assertTrue(revenue_id.depreciation_move_ids)
        self.assertEqual(len(revenue_id.depreciation_move_ids.ids), 5)
        self.assertNotIn('"posted"', revenue_id.depreciation_move_ids.mapped('state'))

        # Journal Entries Accounting Date
        self.assertEqual(revenue_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '12/31/2023')
        self.assertEqual(revenue_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '12/31/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '12/31/2025')
        self.assertEqual(revenue_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '12/31/2026')
        self.assertEqual(revenue_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '12/31/2027')

        # Revenue Charges per month (To be pay monthly)
        self.assertEqual(revenue_id.depreciation_move_ids[0].amount_total, 25050.46)
        self.assertEqual(revenue_id.depreciation_move_ids[1].amount_total, 25050.46)
        self.assertEqual(revenue_id.depreciation_move_ids[2].amount_total, 25050.46)
        self.assertEqual(revenue_id.depreciation_move_ids[3].amount_total, 25050.46)
        self.assertEqual(revenue_id.depreciation_move_ids[4].amount_total, 25050.48)

        # Cumulative Revenue Amount (Total Paid Amount)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_deprecated_value, 25050.46)
        self.assertEqual(revenue_id.depreciation_move_ids[1].asset_deprecated_value, 50100.92)
        self.assertEqual(revenue_id.depreciation_move_ids[2].asset_deprecated_value, 75151.38)
        self.assertEqual(revenue_id.depreciation_move_ids[3].asset_deprecated_value, 100201.84)
        self.assertEqual(revenue_id.depreciation_move_ids[4].asset_deprecated_value, 125252.32)

        # Next Period Revenue (Remaining Amount to pay)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_remaining_value, 100201.86)
        self.assertEqual(revenue_id.depreciation_move_ids[1].asset_remaining_value, 75151.4)
        self.assertEqual(revenue_id.depreciation_move_ids[2].asset_remaining_value, 50100.94)
        self.assertEqual(revenue_id.depreciation_move_ids[3].asset_remaining_value, 25050.48)
        self.assertEqual(revenue_id.depreciation_move_ids[4].asset_remaining_value, 0.00)

        _logger.info("\n\n=================== Completed Validate Revenue to generate depreciation amount with 5 year ===================\n")

    def test_revenue_by_chart_of_accounts_with_create_in_draft(self):
        """
        Test Case for Create Deferred Revenue by creating Deferred Revenue Model and attached with Char of Account.
        - Create Deferred Revenue Model
        - Attach deferred revenue model with COA for draft state

        In this case,
        Original Amount = 12500
        Interval Period = 3 Months
        First Recognition Date = 31/12/2023
        """
        _logger.info("\n\n=================== Started Create Revenue by Char of Accounts with create in draft option ===================\n")

        revenue_model_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale',
                                                     interval_period='months', interval=3, state='model', current_date='2023-12-01')
        self.sale_coa_id.create_asset = 'draft'
        self.sale_coa_id.asset_model_id = revenue_model_id.id

        # Create Customer Invoice with selected COA
        move_id = self.create_invoice(move_type='out_invoice', invoice_amount=12500, coa_id=self.sale_coa_id, date_invoice='2023-12-15')
        move_id.with_context(dict(_test_current_date=datetime.strptime(CURRENT_DATE, '%Y-%m-%d').date())).action_post()

        self.assertTrue(move_id.account_asset_ids)
        self.assertEqual(len(move_id.account_asset_ids.ids), 1)
        self.assertEqual(move_id.account_asset_ids[0].state, 'draft')
        self.assertEqual(move_id.account_asset_ids[0].acquisition_date.strftime(DATETIME_FORMAT), '12/15/2023')
        self.assertEqual(move_id.account_asset_ids[0].original_value, 12500)
        self.assertEqual(move_id.account_asset_ids[0].first_recognition_date.strftime(DATETIME_FORMAT), '12/31/2023')
        self.assertEqual(move_id.account_asset_ids[0].interval_period, 'months')
        self.assertEqual(move_id.account_asset_ids[0].recognition_interval, 3)
        self.assertEqual(move_id.account_asset_ids[0].residual_amount, 12500)

        _logger.info("\n\n=================== Completed Create Revenue by Char of Accounts with create in draft option ===================\n")

    def test_revenue_by_chart_of_accounts_with_create_and_validate(self):
        """
        Test Case for Create Deferred Revenue by creating Deferred Revenue Model and attached with Char of Account.
        - Create Deferred Revenue Model
        - Attach deferred revenue model with COA for create and validate state

        In this case,
        Original Amount = 12500
        Interval Period = 3 Months
        First Recognition Date = 31/12/2023
        """
        _logger.info("\n\n=================== Started Create Revenue by Char of Accounts with create and validate option ===================\n")

        revenue_model_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale',
                                                     interval_period='months', interval=3, state='model')
        self.sale_coa_id.create_asset = 'validate'
        self.sale_coa_id.asset_model_id = revenue_model_id.id

        # Create Customer Invoice with selected COA
        move_id = self.create_invoice(move_type='out_invoice', invoice_amount=12500, coa_id=self.sale_coa_id)
        move_id.with_context(dict(_test_current_date=datetime.strptime(CURRENT_DATE, '%Y-%m-%d').date())).action_post()

        self.assertTrue(move_id.account_asset_ids)
        self.assertEqual(len(move_id.account_asset_ids.ids), 1)
        self.assertEqual(move_id.account_asset_ids[0].state, 'running')
        self.assertEqual(move_id.account_asset_ids[0].original_value, 12500)
        self.assertEqual(move_id.account_asset_ids[0].first_recognition_date.strftime(DATETIME_FORMAT), '12/31/2023')
        self.assertEqual(move_id.account_asset_ids[0].interval_period, 'months')
        self.assertEqual(move_id.account_asset_ids[0].recognition_interval, 3)
        self.assertEqual(move_id.account_asset_ids[0].residual_amount, 12500)

        # Depreciation Lines
        self.assertTrue(move_id.account_asset_ids[0].depreciation_move_ids)
        self.assertEqual(len(move_id.account_asset_ids[0].depreciation_move_ids.ids), 3)

        _logger.info("\n\n=================== Completed Create Revenue by Char of Accounts with create and validate option ===================\n")

    def test_revenue_by_chart_of_accounts_with_create_and_validate_prorata(self):
        """
        Test Case for Create Deferred Revenue by creating Deferred Revenue Model and attached with Char of Account.
        - Create Deferred Revenue Model
        - Attach deferred revenue model with COA for create and validate state

        In this case,
        Prorata = True
        Original Amount = 12500
        Interval Period = 3 Months
        First Recognition Date = 31/12/2023
        """
        _logger.info("\n\n=================== Started Create Revenue by Char of Accounts with create and validate option and prorata enabled ===================\n")

        revenue_model_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale',
                                                     interval_period='months', interval=3, state='model', prorata=True)
        self.sale_coa_id.create_asset = 'validate'
        self.sale_coa_id.asset_model_id = revenue_model_id.id

        # Create Customer Invoice with selected COA
        move_id = self.create_invoice(move_type='out_invoice', invoice_amount=12500, coa_id=self.sale_coa_id)
        move_id.action_post()

        self.assertTrue(move_id.account_asset_ids)
        self.assertEqual(move_id.account_asset_ids[0].prorata, True)

        # Depreciation Lines
        self.assertTrue(move_id.account_asset_ids[0].depreciation_move_ids)
        self.assertEqual(len(move_id.account_asset_ids[0].depreciation_move_ids.ids), 4)

        _logger.info("\n\n=================== Completed Create Revenue by Char of Accounts with create and validate option and prorata enabled ===================\n")

    def test_revenue_all_journal_entries_posted(self):
        """
        Test case for State change to "Closed" when all the journal entries are posted.

        In this case,
        Original Amount = 7000
        Interval Period = 3 Months
        First Recognition Date = 31/12/2023
        """
        _logger.info("\n\n=================== Started Residual Amount With post any Journal Entries (State Closed) ===================\n")

        revenue_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale', original_value=7000,
                                               interval_period='months', interval=3, first_recognition_date='2023-12-31', current_date='2023-12-01')

        self.assertEqual(revenue_id.state, "draft")
        self.assertFalse(revenue_id.depreciation_move_ids)

        # Validate Revenue
        revenue_id.button_confirm()

        self.assertEqual(revenue_id.state, "running")
        self.assertTrue(revenue_id.depreciation_move_ids)
        self.assertEqual(len(revenue_id.depreciation_move_ids.ids), 3)

        for move_line in revenue_id.depreciation_move_ids:
            move_line.write({'auto_post': False})
            move_line.action_post()

        # State Change when all entries are posted
        self.assertEqual(revenue_id.residual_amount, 0.00)
        self.assertEqual(revenue_id.state, "close")

        _logger.info("\n\n=================== Completed Residual Amount With post any Journal Entries (State Closed) ===================\n")

    def test_revenue_posted_entries_with_prorata_three_months_past_dates(self):
        """
        Test case for Past Date's journal entries will be Auto Posted on confirmation of the revenues.

        In this case,
        Interval Period = 3 Months
        Original Value = 2,28,780.56
        Prorata = True
        Prorata Date = 15/10/2023
        First Recognition Date = 31/10/2023
        """
        _logger.info("\n\n=================== Started Validate Revenue to generate depreciation amount with Prorata 3 Months for past dates ===================\n")

        revenue_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale', original_value=228780.56,
                                               interval_period='months', interval=3, first_recognition_date='2023-10-31', prorata=True, prorata_date='2023-10-15', acquisition_date='2023-10-15',
                                               current_date='2023-12-01')

        self.assertEqual(revenue_id.state, "draft")
        self.assertFalse(revenue_id.depreciation_move_ids)

        # Compute Revenue
        revenue_id.button_compute_depreciation_board()

        self.assertEqual(revenue_id.state, "draft")
        self.assertTrue(revenue_id.depreciation_move_ids)
        self.assertEqual(len(revenue_id.depreciation_move_ids.ids), 4)
        self.assertEqual(revenue_id.depreciation_move_ids[0].state, 'draft')
        self.assertEqual(revenue_id.depreciation_move_ids[1].state, 'draft')
        self.assertEqual(revenue_id.depreciation_move_ids[2].state, 'draft')
        self.assertEqual(revenue_id.residual_amount, 228780.56)

        # Compute Revenue
        revenue_id.button_confirm()

        self.assertEqual(revenue_id.depreciation_move_ids[3].state, 'posted')
        self.assertEqual(revenue_id.depreciation_move_ids[2].state, 'posted')
        self.assertEqual(revenue_id.depreciation_move_ids[1].state, 'draft')
        self.assertEqual(revenue_id.depreciation_move_ids[0].state, 'draft')

        # Journal Entries Accounting Date
        self.assertEqual(revenue_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '10/31/2023')
        self.assertEqual(revenue_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '11/30/2023')
        self.assertEqual(revenue_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '12/31/2023')
        self.assertEqual(revenue_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '01/31/2024')

        # Revenue Charges per month (To be pay monthly)
        self.assertEqual(revenue_id.depreciation_move_ids[3].amount_total, 41820.10)
        self.assertEqual(revenue_id.depreciation_move_ids[2].amount_total, 76260.19)
        self.assertEqual(revenue_id.depreciation_move_ids[1].amount_total, 76260.19)
        self.assertEqual(revenue_id.depreciation_move_ids[0].amount_total, 34440.08)

        # Cumulative Revenue Amount (Total Paid Amount)
        self.assertEqual(revenue_id.depreciation_move_ids[3].asset_deprecated_value, 41820.10)
        self.assertEqual(revenue_id.depreciation_move_ids[2].asset_deprecated_value, 118080.29)
        self.assertEqual(revenue_id.depreciation_move_ids[1].asset_deprecated_value, 194340.48)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_deprecated_value, 228780.56)

        # Next Period Revenue (Remaining Amount to pay)
        self.assertEqual(revenue_id.depreciation_move_ids[3].asset_remaining_value, 186960.46)
        self.assertEqual(revenue_id.depreciation_move_ids[2].asset_remaining_value, 110700.27)
        self.assertEqual(revenue_id.depreciation_move_ids[1].asset_remaining_value, 34440.08)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_remaining_value, 0.00)

        # Residual Amount
        self.assertEqual(revenue_id.residual_amount, 110700.27)

        _logger.info("\n\n=================== Completed Validate Revenue to generate depreciation amount with Prorata 3 Months for past dates ===================\n")

    def test_revenue_by_chart_of_accounts_with_no_option(self):
        """
        Test case for New deferred revenue will not be create if COA has "NO" for assets.

        In this case,
        Interval Period = 3 Years
        Original Value = 2,28,780.56
        """
        _logger.info("\n\n=================== Started Validate not create deferred revenue when COA has No for create assets ===================\n")

        revenue_model_id = self.create_account_asset("Test Deferred Expense", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale',
                                                     interval_period='years', interval=3, state='model')

        self.sale_coa_id.asset_model_id = revenue_model_id.id

        # Create Customer Invoice with selected COA
        move_id = self.create_invoice(move_type='out_invoice', invoice_amount=228780.56, coa_id=self.sale_coa_id)
        move_id.action_post()

        self.assertFalse(move_id.account_asset_ids)

        _logger.info("\n\n=================== Completed Validate not create deferred revenue when COA has No for create assets ===================\n")

    def test_revenue_set_to_draft(self):
        """
        Test case for do "Set to Draft", while move record in draft then all created journal entries will be unlinked.

        In this case,
        Original Amount = 7000
        Interval Period = 3 Months
        First Recognition Date = 31/12/2023
        """
        _logger.info("\n\n=================== Started Revenue Set to Draft ===================\n")
        revenue_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale', original_value=7000,
                                               interval_period='months', interval=3, first_recognition_date='2023-12-31', current_date='2023-12-01')

        self.assertEqual(revenue_id.state, "draft")
        self.assertFalse(revenue_id.depreciation_move_ids)

        # Validate Revenue
        revenue_id.button_confirm()
        deprecated_list = revenue_id.depreciation_move_ids.ids

        self.assertEqual(revenue_id.state, "running")
        self.assertTrue(deprecated_list)
        self.assertEqual(len(deprecated_list), 3)

        # Draft Revenue
        revenue_id.button_set_to_draft()

        # Again Validate Revenue
        revenue_id.button_confirm()
        journal_ids = self.env['account.move'].browse(deprecated_list).exists()

        self.assertFalse(journal_ids.ids)

        _logger.info("\n\n=================== Completed Revenue Set to Draft ===================\n")

    def test_revenue_validate_depreciation_lines_for_prorata_entry_equal_installment(self):
        """
        Test case for check Prorata Entry should not be entered if prorata Entry is equal to installment amount.

        In this case,
        Interval Period = 5 Months
        Original Value = 1,22,780.56
        Prorata = True
        Prorata Date = 01/02/2024
        First Recognition Date = 15/01/2024
        """
        _logger.info("\n\n=================== Started Validate Revenue to Prorata Entry is equal to installment amount ===================\n")

        revenue_id = self.create_account_asset("Test Deferred Revenue", self.revenue_account_id, self.deferred_revenue_account_id, self.journal_id, 'sale', original_value=122780.56,
                                               interval_period='months', interval=5, first_recognition_date='2024-01-15', prorata=True, prorata_date='2024-02-01', current_date=CURRENT_DATE)

        self.assertEqual(revenue_id.state, "draft")
        self.assertFalse(revenue_id.depreciation_move_ids)

        # Compute Revenue
        revenue_id.button_compute_depreciation_board()

        self.assertEqual(revenue_id.state, "draft")
        self.assertTrue(revenue_id.depreciation_move_ids)
        self.assertEqual(len(revenue_id.depreciation_move_ids.ids), 5)
        self.assertNotIn('"posted"', revenue_id.depreciation_move_ids.mapped('state'))
        self.assertEqual(revenue_id.prorata, False)

        # Journal Entries Accounting Date
        self.assertEqual(revenue_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '01/15/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '02/29/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '04/30/2024')
        self.assertEqual(revenue_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '05/31/2024')

        # Revenue Charges per month (To be pay monthly)
        self.assertEqual(revenue_id.depreciation_move_ids[0].amount_total, 24556.11)
        self.assertEqual(revenue_id.depreciation_move_ids[1].amount_total, 24556.11)
        self.assertEqual(revenue_id.depreciation_move_ids[2].amount_total, 24556.11)
        self.assertEqual(revenue_id.depreciation_move_ids[3].amount_total, 24556.11)
        self.assertEqual(revenue_id.depreciation_move_ids[4].amount_total, 24556.12)

        # Cumulative Revenue Amount (Total Paid Amount)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_deprecated_value, 24556.11)
        self.assertEqual(revenue_id.depreciation_move_ids[1].asset_deprecated_value, 49112.22)
        self.assertEqual(revenue_id.depreciation_move_ids[2].asset_deprecated_value, 73668.33)
        self.assertEqual(revenue_id.depreciation_move_ids[3].asset_deprecated_value, 98224.44)
        self.assertEqual(revenue_id.depreciation_move_ids[4].asset_deprecated_value, 122780.56)

        # Next Period Revenue (Remaining Amount to pay)
        self.assertEqual(revenue_id.depreciation_move_ids[0].asset_remaining_value, 98224.45)
        self.assertEqual(revenue_id.depreciation_move_ids[1].asset_remaining_value, 73668.34)
        self.assertEqual(revenue_id.depreciation_move_ids[2].asset_remaining_value, 49112.23)
        self.assertEqual(revenue_id.depreciation_move_ids[3].asset_remaining_value, 24556.12)
        self.assertEqual(revenue_id.depreciation_move_ids[4].asset_remaining_value, 0.0)

        _logger.info("\n\n=================== Completed Validate Revenue to Prorata Entry is equal to installment amount ===================\n")
