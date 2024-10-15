from odoo.tests.common import tagged
from odoo.addons.ics_report_base_account.tests.common import AccountReportTestCommon


@tagged('post_install', '-at_install')
class PartnerAgedReportTest(AccountReportTestCommon):

    _web_report_ref = 'ics_account_reports.ics_reports_aged_partner_account_report'

    @classmethod
    def setup_report_data(cls):
        super().setup_report_data()
        cls.customer_a = cls.create_partner({'name': 'Customer A', 'company_id': False})
        cls.customer_b = cls.create_partner({'name': 'Customer B', 'company_id': False})

    def test_aged_partner_report_period_values(self):
        # Customer A Invoices
        self.invoice_a_1 = self.create_invoice(
            partner_id=self.customer_a.id,
            invoice_amount=5000,
            date_invoice='2024-03-01'
        )
        self.invoice_a_2 = self.create_invoice(
            partner_id=self.customer_a.id,
            invoice_amount=2000,
            date_invoice='2024-04-01'
        )
        self.invoice_a_3 = self.create_invoice(
            partner_id=self.customer_a.id,
            invoice_amount=3000,
            date_invoice='2024-05-01'
        )

        # Doing payment for invoice_a_2 of 1000
        self.register_payment(self.invoice_a_2, 1000, payment_date='2024-05-01', auto_post=True)

        # Customer B
        self.invoice_b_1 = self.create_invoice(
            partner_id=self.customer_b.id,
            invoice_amount=6000,
            date_invoice='2023-12-31'
        )

        self.invoice_b_2 = self.create_invoice(
            partner_id=self.customer_b.id,
            invoice_amount=3000,
            date_invoice='2024-01-05'
        )

        # # Adjusting Payment of 1500 for Invoice B 2
        self.register_payment(self.invoice_b_2, 1500, payment_date='2024-05-01', auto_post=True)

        # Getting report and validating as on date
        self.set_report_options({'filter_date_options': {
            'filter': 'custom',
            'date_to': '2024-05-01'
        }})
        self.report_data = self.get_report_data(context={'report_type': 'receivable'})
        sections = self.report_data.get('sections', [])

        # Section have 3 rows, first two for partner lines and last for group total
        self.assertEqual(len(sections), 3, 'Have three section lines including group total')
        self.assertEqual(sections[-1].get('group_total', False), True, 'Last Section row need to be group total')

        # NOTE THAT, Payment adjusted will not be minus from section as db commit is not done so based on given
        # date of payment calculate amounts
        for section in sections[:-1]:
            if section.get('id') == self.customer_a.id:
                self.assertSectionValueEqual(section, 'period0', 2000, 'Customer A have As on Date due of 2000')
                self.assertSectionValueEqual(section, 'period1', 2000, 'Customer A have period1 (1-30) due of 2000')
                self.assertSectionValueEqual(section, 'period3', 5000, 'Customer A have period2 (31-60) due of 5000')
                self.assertSectionValueEqual(section, 'amount_residual', 9000, 'Customer A have amount due of 9000')
            if section.get('id') == self.customer_b.id:
                self.assertSectionValueEqual(section, 'period0', -1500, 'Customer B have As on Date due of -1500')
                self.assertSectionValueEqual(section, 'period5', 6000, 'Customer B have As on Date due of 6000')
                self.assertSectionValueEqual(section, 'amount_residual', 7500, 'Customer A have amount due of 7500')

        self.assertSectionValueEqual(sections[-1], 'period0', 500, 'Group Total have period0 As On due of 500')
        self.assertSectionValueEqual(sections[-1], 'period1', 2000, 'Group Total have period0 (1-30) due of 2000')
        self.assertSectionValueEqual(sections[-1], 'period2', 0, 'Group Total have period0 (31-60) due of 0')
        self.assertSectionValueEqual(sections[-1], 'period3', 5000, 'Group Total have period0 (61-90) due of 5000')

        # Getting report and validating for last month
        self.set_report_options({'filter_date_options': {
            'filter': 'custom',
            'date_to': '2024-04-01'
        }})
        self.report_data = self.get_report_data(context={'report_type': 'receivable'})
        sections = self.report_data.get('sections', [])

        # Section have 3 rows, first two for partner lines and last for group total
        self.assertEqual(len(sections), 3, 'Have three section lines including group total')
        self.assertEqual(sections[-1].get('group_total', False), True, 'Last Section row need to be group total')

        # NOTE THAT, Payment adjusted will not be minus from section as db commit is not done so based on given
        # date of payment calculate amounts
        for section in sections[:-1]:
            if section.get('id') == self.customer_a.id:
                self.assertSectionValueEqual(section, 'period0', 2000, 'Customer A have As on Date due of 2000')
                self.assertSectionValueEqual(section, 'period1', 0, 'Customer A have period1 (1-30) due of 0')
                self.assertSectionValueEqual(section, 'period2', 5000, 'Customer A have period2 (31-60) due of 5000')
                self.assertSectionValueEqual(section, 'period3', 0, 'Customer A have period3 (61-90) due of 0')
                self.assertSectionValueEqual(section, 'amount_residual', 7000, 'Customer A have amount due of 10000')
            if section.get('id') == self.customer_b.id:
                self.assertSectionValueEqual(section, 'period0', 0, 'Customer B have As on Date due of 0')
                self.assertSectionValueEqual(section, 'period5', 0, 'Customer B have As on Date due of 0')
                self.assertSectionValueEqual(section, 'amount_residual', 9000, 'Customer B have amount due of 9000')

        self.assertSectionValueEqual(sections[-1], 'period0', 2000, 'Group Total have period0 As On due of 2000')
        self.assertSectionValueEqual(sections[-1], 'period1', 0, 'Group Total have period0 (1-30) due of 0')
        self.assertSectionValueEqual(sections[-1], 'period2', 5000, 'Group Total have period1 (31-60) due of 5000')
        self.assertSectionValueEqual(sections[-1], 'amount_residual', 16000, 'Group Total have amount_residual due of 16000')
