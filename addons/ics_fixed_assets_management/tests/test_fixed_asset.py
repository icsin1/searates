# -*- coding: utf-8 -*-

import logging
from odoo.tests import Form
from datetime import date, datetime
from odoo.addons.ics_account_deferred_revenue_expense.tests.common import ICSAccountDeferredCommon, CURRENT_DATE

_logger = logging.getLogger(__name__)
DATETIME_FORMAT = '%m/%d/%Y'


class TestFixedAsset(ICSAccountDeferredCommon):

    def setUp(self):
        super().setUp()
        self.company = self.company_data.get('company')

        # Setup Account Data
        self.account_asset_id = self.env['account.account'].search([
            ('company_id', '=', self.company_data['company'].id),
            ('user_type_id', '=', self.env.ref('account.data_account_type_fixed_assets').id)
        ], limit=1)

    @classmethod
    def create_fixed_asset(cls, name, depreciation_id, depreciation_expense_id, account_asset_id, journal_id, asset_type, **kw):
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
        asset_form.account_asset_id = account_asset_id
        if kw.get('original_value'):
            asset_form.original_value = kw.get('original_value')
        if kw.get('interval_period'):
            asset_form.interval_period = kw.get('interval_period')
        if kw.get('recognition_interval'):
            asset_form.recognition_interval = kw.get('recognition_interval')
        if kw.get('first_recognition_date'):
            asset_form.first_recognition_date = kw.get('first_recognition_date')
        if kw.get('prorata'):
            asset_form.prorata = kw.get('prorata')
        if kw.get('prorata_date'):
            asset_form.prorata_date = kw.get('prorata_date')
        if kw.get('acquisition_date'):
            asset_form.acquisition_date = kw.get('acquisition_date')
        if kw.get('method'):
            asset_form.method = kw.get('method')
        if kw.get('declining_factor'):
            asset_form.declining_factor = kw.get('declining_factor')
        if kw.get('non_depreciable_value'):
            asset_form.non_depreciable_value = kw.get('non_depreciable_value')
        return asset_form.save()

    def setup_char_of_account_data(self):
        """
        Create Char of Account "Fixed Asset" type record
        """
        purchase_coa_id = self.env['account.account'].create({
            'code': 100213,
            'name': "Fixed Asset",
            'user_type_id': self.env.ref('account.data_account_type_fixed_assets').id
        })
        return purchase_coa_id

    def test_cases_01(self):
        """
        Test cases for, Check depreciation lines for straight line method without Not Depreciable Value.

        Method = Straight Line
        Interval = 5 Years
        Current Date = 2023-12-01
        Original Value = 10,000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date=CURRENT_DATE, recognition_interval=5, interval_period='years')
        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.residual_amount, 10000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 5)

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '03/31/2025')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '03/31/2026')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '03/31/2027')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '03/31/2028')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 2000)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 4000)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 6000)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 8000)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 10000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 8000)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 6000)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 4000)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 0.00)

    def test_cases_02(self):
        """
        Test cases for, Check depreciation lines for straight line method with Not Depreciable Value.

        Method = Straight Line
        Interval = 5 Years
        Current Date = 2023-12-01
        Original Value = 10,000
        Not Depreciable Value = 1000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date=CURRENT_DATE, recognition_interval=5, interval_period='years', non_depreciable_value=1000)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.original_value, 10000)
        self.assertEqual(asset_id.residual_amount, 9000)
        self.assertEqual(asset_id.book_value, 10000)
        self.assertEqual(asset_id.non_depreciable_value, 1000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 5)

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '03/31/2025')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '03/31/2026')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '03/31/2027')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '03/31/2028')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 1800)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 1800)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1800)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 1800)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 1800)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 1800)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 3600)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 5400)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 7200)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 9000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 7200)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 5400)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 3600)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 1800)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 0.00)

    def test_cases_03(self):
        """
        Test cases for, Check depreciation lines for Declining method without Not Depreciable Value.

        Method = Declining
        Interval = 5 Years
        Current Date = 2023-12-01
        Original Value = 10,000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset',
                                           original_value=10000, current_date=CURRENT_DATE, recognition_interval=5,
                                           interval_period='years', method='decline', declining_factor=30)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.residual_amount, 10000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 5)

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '03/31/2025')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '03/31/2026')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '03/31/2027')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '03/31/2028')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 3000)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 2100)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1470)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 1029)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 2401)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 3000)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 5100)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 6570)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 7599)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 10000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 7000)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 4900)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 3430)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 2401)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 0.00)

    def test_cases_04(self):
        """
        Test cases for, Check depreciation lines for Declining method with Not Depreciable Value.

        Method = Declining
        Interval = 5 Years
        Current Date = 2023-12-01
        Original Value = 10,000
        Declining Factor = 30
        Not Depreciable Value = 1000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id,
                                           self.expense_account_id, self.account_asset_id, self.journal_id,
                                           'asset', original_value=10000, current_date=CURRENT_DATE,
                                           recognition_interval=5, interval_period='years', method='decline',
                                           declining_factor=30, non_depreciable_value=1000)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.original_value, 10000)
        self.assertEqual(asset_id.residual_amount, 9000)
        self.assertEqual(asset_id.book_value, 10000)
        self.assertEqual(asset_id.non_depreciable_value, 1000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 5)

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '03/31/2025')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '03/31/2026')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '03/31/2027')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '03/31/2028')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 2700)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 1890)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1323)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 926.1)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 2160.9)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 2700)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 4590)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 5913)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 6839.1)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 9000)

        # # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 6300)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 4410)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 3087)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 2160.9)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 0.00)

    def test_cases_05(self):
        """
        Test cases for, Check depreciation lines for straight line method with Prorata.

        Method = Straight Line
        Interval = 5 Years
        Current Date = 2023-12-01
        Original Value = 10,000
        Prorata = True
        Prorata Date = '12/15/2023'
        First Recognition Date = '01/15/2024'
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date=CURRENT_DATE, recognition_interval=5, interval_period='years',
                                           prorata=True, prorata_date='2023-12-15', first_recognition_date='2024-01-15')

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.residual_amount, 10000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 6)
        self.assertEqual(asset_id.first_recognition_date.strftime(DATETIME_FORMAT), '01/15/2024')

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '01/15/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '01/15/2025')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '01/15/2026')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '01/15/2027')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '01/15/2028')
        self.assertEqual(asset_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '01/15/2029')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 590.16)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[5].amount_total, 1409.84)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 590.16)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 2590.16)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 4590.16)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 6590.16)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 8590.16)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_deprecated_value, 10000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 9409.84)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 7409.84)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 5409.84)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 3409.84)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 1409.84)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_remaining_value, 0)

    def test_cases_06(self):
        """
        Test cases for, Check depreciation lines for straight line method with Prorata and with Not depreciated value.

        Method = Straight Line
        Interval = 5 Years
        Current Date = 2023-12-01
        Original Value = 10,000
        Prorata = True
        Prorata Date = '12/15/2023'
        First Recognition Date = '01/15/2024'
        Not Depreciable Value = 1000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date=CURRENT_DATE, recognition_interval=5, interval_period='years',
                                           prorata=True, prorata_date='2023-12-15', first_recognition_date='2024-01-15',
                                           non_depreciable_value=1000)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.original_value, 10000)
        self.assertEqual(asset_id.residual_amount, 9000)
        self.assertEqual(asset_id.book_value, 10000)
        self.assertEqual(asset_id.non_depreciable_value, 1000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 6)
        self.assertEqual(asset_id.first_recognition_date.strftime(DATETIME_FORMAT), '01/15/2024')

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '01/15/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '01/15/2025')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '01/15/2026')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '01/15/2027')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '01/15/2028')
        self.assertEqual(asset_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '01/15/2029')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 531.15)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 1800)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1800)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 1800)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 1800)
        self.assertEqual(asset_id.depreciation_move_ids[5].amount_total, 1268.8500000000001)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 531.15)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 2331.15)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 4131.15)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 5931.15)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 7731.15)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_deprecated_value, 9000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 8468.85)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 6668.85)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 4868.85)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 3068.85)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 1268.85)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_remaining_value, 0)

    def test_cases_07(self):
        """
        Test cases for, Check depreciation lines for Declining method with Prorata.

        Method = Declining
        Interval = 5 Years
        Current Date = 2023-12-01
        Original Value = 10,000
        Declining Factor = 30
        Not Depreciable Value = 1000
        Prorata = True
        Prorata Date = '12/15/2023'
        First Recognition Date = '01/15/2024'
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date=CURRENT_DATE, recognition_interval=5, interval_period='years',
                                           prorata=True, prorata_date='2023-12-15', first_recognition_date='2024-01-15',
                                           method='decline', declining_factor=30)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.original_value, 10000)
        self.assertEqual(asset_id.residual_amount, 10000)
        self.assertEqual(asset_id.book_value, 10000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 6)
        self.assertEqual(asset_id.first_recognition_date.strftime(DATETIME_FORMAT), '01/15/2024')

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '01/15/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '01/15/2025')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '01/15/2026')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '01/15/2027')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '01/15/2028')
        self.assertEqual(asset_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '01/15/2029')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 885.25)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 2734.42)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1914.1000000000001)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 1339.8700000000001)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 937.91)
        self.assertEqual(asset_id.depreciation_move_ids[5].amount_total, 2188.4500000000003)
        #
        # # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 885.25)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 3619.67)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 5533.77)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 6873.64)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 7811.55)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_deprecated_value, 10000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 9114.75)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 6380.33)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 4466.23)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 3126.36)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 2188.45)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_remaining_value, 0)

    def test_cases_08(self):
        """
        Test cases for, Check depreciation lines for Declining method with Prorata and non depreciated value.

        Method = Declining
        Interval = 5 Years
        Current Date = 2023-12-01
        Original Value = 10,000
        Declining Factor = 30
        Not Depreciable Value = 1000
        Prorata = True
        Prorata Date = '12/15/2023'
        First Recognition Date = '01/15/2024'
        Not Depreciable Value = 1000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date=CURRENT_DATE, recognition_interval=5, interval_period='years',
                                           prorata=True, prorata_date='2023-12-15', first_recognition_date='2024-01-15',
                                           method='decline', declining_factor=30, non_depreciable_value=1000)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.original_value, 10000)
        self.assertEqual(asset_id.residual_amount, 9000)
        self.assertEqual(asset_id.book_value, 10000)
        self.assertEqual(asset_id.non_depreciable_value, 1000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 6)
        self.assertEqual(asset_id.first_recognition_date.strftime(DATETIME_FORMAT), '01/15/2024')

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '01/15/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '01/15/2025')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '01/15/2026')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '01/15/2027')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '01/15/2028')
        self.assertEqual(asset_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '01/15/2029')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 796.72)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 2460.98)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1722.69)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 1205.88)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 844.12)
        self.assertEqual(asset_id.depreciation_move_ids[5].amount_total, 1969.6100000000001)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 796.72)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 3257.7)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 4980.39)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 6186.27)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 7030.39)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_deprecated_value, 9000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 8203.28)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 5742.3)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 4019.61)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 2813.73)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 1969.61)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_remaining_value, 0)

    def test_cases_09(self):
        """
        Test cases for, Check depreciation lines for straight line method without Not Depreciable Value.

        Method = Straight Line
        Interval = 6 Months
        Current Date = 2023-12-01
        Original Value = 10,000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date=CURRENT_DATE, recognition_interval=6, interval_period='months')

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.residual_amount, 10000)
        self.assertEqual(asset_id.book_value, 10000)
        self.assertEqual(asset_id.non_depreciable_value, 0)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 6)

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '12/31/2023')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '01/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '02/29/2024')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '04/30/2024')
        self.assertEqual(asset_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '05/31/2024')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 1666.67)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 1666.67)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1666.67)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 1666.67)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 1666.67)
        self.assertEqual(asset_id.depreciation_move_ids[5].amount_total, 1666.65)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 1666.67)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 3333.34)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 5000.01)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 6666.68)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 8333.35)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_deprecated_value, 10000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 8333.33)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 6666.66)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 4999.99)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 3333.32)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 1666.65)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_remaining_value, 0.00)

    def test_cases_10(self):
        """
        Test cases for, Check depreciation lines for straight line method with Not Depreciable Value.

        Method = Straight Line
        Interval = 6 Months
        Current Date = 2023-12-01
        Original Value = 10,000
        Not Depreciable Value = 1000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date=CURRENT_DATE, recognition_interval=6, interval_period='months', non_depreciable_value=1000)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.original_value, 10000)
        self.assertEqual(asset_id.residual_amount, 9000)
        self.assertEqual(asset_id.book_value, 10000)
        self.assertEqual(asset_id.non_depreciable_value, 1000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 6)

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '12/31/2023')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '01/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '02/29/2024')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '04/30/2024')
        self.assertEqual(asset_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '05/31/2024')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 1500)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 1500)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1500)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 1500)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 1500)
        self.assertEqual(asset_id.depreciation_move_ids[5].amount_total, 1500)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 1500)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 3000)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 4500)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 6000)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 7500)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_deprecated_value, 9000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 7500)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 6000)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 4500)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 3000)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 1500)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_remaining_value, 0.00)

    def test_cases_11(self):
        """
        Test cases for, Check depreciation lines for Declining method without Not Depreciable Value.

        Method = Declining
        Interval = 6 Months
        Current Date = 2023-12-01
        Original Value = 10,000
        Declining Factor = 20
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset',
                                           original_value=15500, current_date=CURRENT_DATE, recognition_interval=6,
                                           interval_period='months', method='decline', declining_factor=20)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.residual_amount, 15500)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 6)

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '12/31/2023')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '01/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '02/29/2024')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '04/30/2024')
        self.assertEqual(asset_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '05/31/2024')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 3100)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 2480)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1984)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 1587.2)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 1269.76)
        self.assertEqual(asset_id.depreciation_move_ids[5].amount_total, 5079.04)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 3100)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 5580)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 7564)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 9151.2)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 10420.96)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_deprecated_value, 15500)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 12400)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 9920)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 7936)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 6348.8)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 5079.04)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_remaining_value, 0.00)

    def test_cases_12(self):
        """
        Test cases for, Check depreciation lines for Declining method with Not Depreciable Value.

        Method = Declining
        Interval = 6 Months
        Current Date = 2023-12-01
        Original Value = 14320
        Declining Factor = 35
        Not Depreciable Value = 1000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id,
                                           self.expense_account_id, self.account_asset_id, self.journal_id,
                                           'asset', original_value=14320, current_date=CURRENT_DATE,
                                           recognition_interval=6, interval_period='months', method='decline',
                                           declining_factor=35, non_depreciable_value=1000)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.original_value, 14320)
        self.assertEqual(asset_id.residual_amount, 13320)
        self.assertEqual(asset_id.book_value, 14320)
        self.assertEqual(asset_id.non_depreciable_value, 1000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 6)

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '12/31/2023')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '01/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '02/29/2024')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '04/30/2024')
        self.assertEqual(asset_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '05/31/2024')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 4662)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 3030.3)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1969.69)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 1280.30)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 832.2)
        self.assertEqual(asset_id.depreciation_move_ids[5].amount_total, 1545.51)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 4662)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 7692.3)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 9661.99)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 10942.29)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 11774.49)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_deprecated_value, 13320)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 8658)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 5627.7)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 3658.01)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 2377.71)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 1545.51)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_remaining_value, 0.00)

    def test_cases_13(self):
        """
        Test cases for, Check depreciation lines for straight line method with Prorata and with Not depreciated value.

        Method = Straight Line
        Interval = 6 Months
        Current Date = 2023-12-01
        Original Value = 47,680
        Prorata = True
        Prorata Date = '12/15/2023'
        First Recognition Date = '01/15/2024'
        Not Depreciable Value = 580
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=47680,
                                           current_date=CURRENT_DATE, recognition_interval=6, interval_period='months',
                                           prorata=True, prorata_date='2023-12-15', first_recognition_date='2024-01-15',
                                           non_depreciable_value=580)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.original_value, 47680)
        self.assertEqual(asset_id.residual_amount, 47100)
        self.assertEqual(asset_id.book_value, 47680)
        self.assertEqual(asset_id.non_depreciable_value, 580)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 7)
        self.assertEqual(asset_id.first_recognition_date.strftime(DATETIME_FORMAT), '01/15/2024')

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '01/15/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '02/29/2024')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '04/30/2024')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '05/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '06/30/2024')
        self.assertEqual(asset_id.depreciation_move_ids[6].date.strftime(DATETIME_FORMAT), '07/31/2024')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 4304.84)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 7850)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 7850)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 7850)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 7850)
        self.assertEqual(asset_id.depreciation_move_ids[5].amount_total, 7850)
        self.assertEqual(asset_id.depreciation_move_ids[6].amount_total, 3545.16)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 4304.84)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 12154.84)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 20004.84)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 27854.84)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 35704.84)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_deprecated_value, 43554.84)
        self.assertEqual(asset_id.depreciation_move_ids[6].asset_deprecated_value, 47100)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 42795.16)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 34945.16)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 27095.16)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 19245.16)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 11395.16)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_remaining_value, 3545.16)
        self.assertEqual(asset_id.depreciation_move_ids[6].asset_remaining_value, 0)

    def test_cases_14(self):
        """
        Test cases for, Check depreciation lines for Declining method with Prorata and non depreciated value.

        Method = Declining
        Interval = 6 Months
        Current Date = 2023-12-01
        Original Value = 10,000
        Declining Factor = 15
        Not Depreciable Value = 1000
        Prorata = True
        Prorata Date = '12/15/2023'
        First Recognition Date = '01/15/2024'
        Not Depreciable Value = 1000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=9946.67,
                                           current_date=CURRENT_DATE, recognition_interval=6, interval_period='months',
                                           prorata=True, prorata_date='2023-12-15', first_recognition_date='2024-01-15',
                                           method='decline', declining_factor=15, non_depreciable_value=1000)

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.original_value, 9946.67)
        self.assertEqual(asset_id.residual_amount, 8946.67)
        self.assertEqual(asset_id.book_value, 9946.67)
        self.assertEqual(asset_id.non_depreciable_value, 1000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 7)
        self.assertEqual(asset_id.first_recognition_date.strftime(DATETIME_FORMAT), '01/15/2024')

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '01/15/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '02/29/2024')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '04/30/2024')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '05/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[5].date.strftime(DATETIME_FORMAT), '06/30/2024')
        self.assertEqual(asset_id.depreciation_move_ids[6].date.strftime(DATETIME_FORMAT), '07/31/2024')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 735.94)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 1231.6100000000001)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 1046.8700000000001)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 889.84)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 756.36)
        self.assertEqual(asset_id.depreciation_move_ids[5].amount_total, 642.91)
        self.assertEqual(asset_id.depreciation_move_ids[6].amount_total, 3643.14)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 735.94)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 1967.55)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 3014.42)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 3904.26)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 4660.62)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_deprecated_value, 5303.53)
        self.assertEqual(asset_id.depreciation_move_ids[6].asset_deprecated_value, 8946.67)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 8210.73)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 6979.12)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 5932.25)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 5042.41)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 4286.05)
        self.assertEqual(asset_id.depreciation_move_ids[5].asset_remaining_value, 3643.14)
        self.assertEqual(asset_id.depreciation_move_ids[6].asset_remaining_value, 0)

    def test_cases_15(self):
        """
        Test cases for, Post entries manually with Not depreciable amount.

        Method = Straight Line
        Interval = 5 Years
        Current Date = 2023-12-01
        Original Value = 10,000
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date=CURRENT_DATE, recognition_interval=5, interval_period='years', non_depreciable_value=500)

        self.assertEqual(asset_id.state, "draft")

        # Validate Asset
        asset_id.button_confirm()

        self.assertEqual(asset_id.state, "running")
        self.assertEqual(asset_id.book_value, 10000)
        self.assertEqual(asset_id.non_depreciable_value, 500)
        self.assertEqual(asset_id.residual_amount, 9500)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 5)

        for move_line in asset_id.depreciation_move_ids:
            move_line.write({'auto_post': False})

        # Post 1st journal entry
        asset_id.depreciation_move_ids[0].action_post()
        self.assertEqual(asset_id.residual_amount, 7600)
        self.assertEqual(asset_id.book_value, 8100)

        # Post 2nd journal entry
        asset_id.depreciation_move_ids[1].action_post()
        self.assertEqual(asset_id.residual_amount, 5700)
        self.assertEqual(asset_id.book_value, 6200)

        # Post 3rd journal entry
        asset_id.depreciation_move_ids[2].action_post()
        self.assertEqual(asset_id.residual_amount, 3800)
        self.assertEqual(asset_id.book_value, 4300)

        # Post 4th journal entry
        asset_id.depreciation_move_ids[3].action_post()
        self.assertEqual(asset_id.residual_amount, 1900)
        self.assertEqual(asset_id.book_value, 2400)

        # Post 5th journal entry
        asset_id.depreciation_move_ids[4].action_post()
        self.assertEqual(asset_id.residual_amount, 0)
        self.assertEqual(asset_id.book_value, 500)
        self.assertEqual(asset_id.state, "close")

    def test_cases_16(self):
        """
        Test cases for, Past Dates Journal Entries for Declining by months.

        Method = Declining
        Interval = 3 Months
        Current Date = 2023-12-01
        Original Value = 228780.56
        First Recognition Date = 31/10/2023
        Declining Factor = 12
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', first_recognition_date='2023-10-31',
                                           original_value=228780.56, current_date=CURRENT_DATE, recognition_interval=3,
                                           interval_period='months', method='decline', declining_factor=12)

        # Compute Revenue
        asset_id.button_compute_depreciation_board()
        self.assertEqual(asset_id.state, "draft")
        self.assertEqual(asset_id.book_value, 228780.56)
        self.assertEqual(asset_id.residual_amount, 228780.56)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 3)

        # Validate Asset
        asset_id.button_confirm()
        self.assertEqual(asset_id.state, "running")
        self.assertEqual(asset_id.book_value, 177167.66)
        self.assertEqual(asset_id.residual_amount, 177167.66)
        self.assertEqual(len(asset_id.depreciation_move_ids.filtered(lambda move: move.state == 'posted')), 2)
        self.assertEqual(len(asset_id.depreciation_move_ids.filtered(lambda move: move.state == 'draft')), 1)

    def test_cases_17(self):
        """
        Test cases for, create and validate straight line by chart of account with prorata for months.

        Method = Straight Line
        Interval = 3 Months
        Current Date = 2023-12-01
        Vendor Bill Value = 12,500
        Bill Date = '12/15/2023'
        Prorata = True
        Prorata Date = '12/15/2023'
        """
        purchase_coa_id = self.setup_char_of_account_data()
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset',
                                           current_date=CURRENT_DATE, recognition_interval=3, interval_period='months',
                                           prorata=True, state='model')

        # Add asset in Char of Account of Fixed assets type
        purchase_coa_id.create_asset = 'validate'
        purchase_coa_id.asset_model_id = asset_id.id

        # Create Vendor Bill with selected COA
        move_id = self.create_invoice(move_type='in_invoice', invoice_amount=12500, coa_id=purchase_coa_id, date_invoice='2023-12-15')
        move_id.with_context(dict(_test_current_date=datetime.strptime(CURRENT_DATE, '%Y-%m-%d').date())).action_post()

        self.assertTrue(move_id.account_asset_ids)
        self.assertEqual(len(move_id.account_asset_ids.ids), 1)
        self.assertEqual(move_id.account_asset_ids[0].state, 'running')
        self.assertEqual(move_id.account_asset_ids[0].acquisition_date.strftime(DATETIME_FORMAT), '12/15/2023')
        self.assertEqual(move_id.account_asset_ids[0].original_value, 12500)
        self.assertEqual(move_id.account_asset_ids[0].first_recognition_date.strftime(DATETIME_FORMAT), '12/31/2023')
        self.assertEqual(move_id.account_asset_ids[0].interval_period, 'months')
        self.assertEqual(move_id.account_asset_ids[0].recognition_interval, 3)
        self.assertEqual(move_id.account_asset_ids[0].residual_amount, 12500)
        self.assertEqual(move_id.account_asset_ids[0].book_value, 12500)

        # Depreciation Lines
        self.assertTrue(move_id.account_asset_ids[0].depreciation_move_ids)
        self.assertEqual(len(move_id.account_asset_ids[0].depreciation_move_ids.ids), 4)

        decline_asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                                   self.account_asset_id, self.journal_id, 'asset',
                                                   current_date=CURRENT_DATE, recognition_interval=3, interval_period='months',
                                                   prorata=True, state='model', method='decline', declining_factor=12)

        # Add asset in Char of Account of Fixed assets type
        purchase_coa_id.create_asset = 'draft'
        purchase_coa_id.asset_model_id = decline_asset_id.id

        # Create Vendor Bill with selected COA
        declining_move_id = self.create_invoice(move_type='in_invoice', invoice_amount=12500, coa_id=purchase_coa_id, date_invoice='2023-12-15')
        declining_move_id.with_context(dict(_test_current_date=datetime.strptime(CURRENT_DATE, '%Y-%m-%d').date())).action_post()

        self.assertEqual(declining_move_id.account_asset_ids[0].method, 'decline')
        self.assertEqual(declining_move_id.account_asset_ids[0].declining_factor, 12)

    def test_cases_18(self):
        """
        Test cases for, create and validate straight line by chart of account without manage items.

        Method = Straight Line
        Interval = 3 Months
        Current Date = 2023-12-01
        Vendor Bill Value = 12,500
        Bill Date = '12/15/2023'
        Manage Items = False
        """
        purchase_coa_id = self.setup_char_of_account_data()
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', state='model',
                                           current_date=CURRENT_DATE, recognition_interval=3, interval_period='months')

        # Add asset in Char of Account of Fixed assets type
        purchase_coa_id.create_asset = 'validate'
        purchase_coa_id.asset_model_id = asset_id.id

        # Create Vendor Bill with selected COA
        move_id = self.create_invoice(move_type='in_invoice', invoice_amount=12500, coa_id=purchase_coa_id, date_invoice='2023-12-15')
        move_id.invoice_line_ids = [(0, 0, {
            'name': 'product that cost 10000',
            'quantity': 2,
            'price_unit': 10000,
            'account_id': purchase_coa_id
        })]
        move_id.with_context(dict(_test_current_date=datetime.strptime(CURRENT_DATE, '%Y-%m-%d').date())).action_post()

        self.assertTrue(move_id.account_asset_ids)
        self.assertEqual(len(move_id.account_asset_ids.ids), 2)
        self.assertEqual(move_id.account_asset_ids[0].original_value, 12500)
        self.assertEqual(move_id.account_asset_ids[1].original_value, 20000)

    def test_cases_19(self):
        """
        Test cases for, create and validate straight line by chart of account without manage items.

        Method = Straight Line
        Interval = 3 Months
        Current Date = 2023-12-01
        Vendor Bill Value = 12,500
        Bill Date = '12/15/2023'
        Manage Items = True
        """
        purchase_coa_id = self.setup_char_of_account_data()
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', state='model',
                                           current_date=CURRENT_DATE, recognition_interval=3, interval_period='months')

        # Add asset in Char of Account of Fixed assets type
        purchase_coa_id.create_asset = 'validate'
        purchase_coa_id.asset_model_id = asset_id.id
        purchase_coa_id.manage_asset_per_line = True

        # Create Vendor Bill with selected COA
        move_id = self.create_invoice(move_type='in_invoice', invoice_amount=12500, coa_id=purchase_coa_id, date_invoice='2023-12-15')
        move_id.invoice_line_ids = [(0, 0, {
            'name': 'product that cost 10000',
            'quantity': 2,
            'price_unit': 10000,
            'account_id': purchase_coa_id
        })]
        move_id.with_context(dict(_test_current_date=datetime.strptime(CURRENT_DATE, '%Y-%m-%d').date())).action_post()

        self.assertTrue(move_id.account_asset_ids)
        self.assertEqual(len(move_id.account_asset_ids.ids), 3)
        self.assertEqual(move_id.account_asset_ids[0].original_value, 12500)
        self.assertEqual(move_id.account_asset_ids[1].original_value, 10000)
        self.assertEqual(move_id.account_asset_ids[2].original_value, 10000)

    def test_cases_20(self):
        """
        Test cases for, Check Prorata entry should not be add if prorata date is 1st of month.

        Method = Straight Line
        Interval = 5 Months
        Current Date = 2024-01-02
        Original Value = 10,000
        Prorata = True
        Prorata Date = '01/01/2024'
        First Recognition Date = '03/31/2024'
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date='2024-01-02', recognition_interval=5, interval_period='months',
                                           prorata=True, prorata_date='2024-01-01', first_recognition_date='2024-03-31')

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.residual_amount, 10000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 5)
        self.assertEqual(asset_id.first_recognition_date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[0].ref, 'Test Fixed Asset (1/5)')
        self.assertNotEqual(asset_id.depreciation_move_ids[0].ref, 'Test Fixed Asset (prorata entry)')

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '03/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '04/30/2024')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '05/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '06/30/2024')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '07/31/2024')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 2000)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 4000)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 6000)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 8000)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 10000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 8000)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 6000)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 4000)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 0)

    def test_cases_21(self):
        """
        Test cases for, Check Prorata entry should not be add if prorata date is 1st of month.

        Method = Straight Line
        Interval = 5 Years
        Current Date = 2024-01-02
        Original Value = 10,000
        Prorata = True
        Prorata Date = '04/01/2023'
        First Recognition Date = '04/01/2023'
        """
        asset_id = self.create_fixed_asset("Test Fixed Asset", self.account_asset_id, self.expense_account_id,
                                           self.account_asset_id, self.journal_id, 'asset', original_value=10000,
                                           current_date='2024-01-02', recognition_interval=5, interval_period='years',
                                           prorata=True, prorata_date='2023-04-01', first_recognition_date='2024-01-31')

        asset_id.button_compute_depreciation_board()

        self.assertEqual(asset_id.residual_amount, 10000)
        self.assertEqual(len(asset_id.depreciation_move_ids.ids), 5)
        self.assertEqual(asset_id.first_recognition_date.strftime(DATETIME_FORMAT), '01/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[0].ref, 'Test Fixed Asset (1/5)')
        self.assertNotEqual(asset_id.depreciation_move_ids[0].ref, 'Test Fixed Asset (prorata entry)')

        # Journal Entries Accounting Date
        self.assertEqual(asset_id.depreciation_move_ids[0].date.strftime(DATETIME_FORMAT), '01/31/2024')
        self.assertEqual(asset_id.depreciation_move_ids[1].date.strftime(DATETIME_FORMAT), '01/31/2025')
        self.assertEqual(asset_id.depreciation_move_ids[2].date.strftime(DATETIME_FORMAT), '01/31/2026')
        self.assertEqual(asset_id.depreciation_move_ids[3].date.strftime(DATETIME_FORMAT), '01/31/2027')
        self.assertEqual(asset_id.depreciation_move_ids[4].date.strftime(DATETIME_FORMAT), '01/31/2028')

        # Fixed Asset Charges per month (To be pay monthly)
        self.assertEqual(asset_id.depreciation_move_ids[0].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[1].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[2].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[3].amount_total, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[4].amount_total, 2000)

        # Cumulative Fixed Asset (Total Paid Amount)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_deprecated_value, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_deprecated_value, 4000)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_deprecated_value, 6000)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_deprecated_value, 8000)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_deprecated_value, 10000)

        # Next Period Fixed Asset (Remaining Amount to pay)
        self.assertEqual(asset_id.depreciation_move_ids[0].asset_remaining_value, 8000)
        self.assertEqual(asset_id.depreciation_move_ids[1].asset_remaining_value, 6000)
        self.assertEqual(asset_id.depreciation_move_ids[2].asset_remaining_value, 4000)
        self.assertEqual(asset_id.depreciation_move_ids[3].asset_remaining_value, 2000)
        self.assertEqual(asset_id.depreciation_move_ids[4].asset_remaining_value, 0)
