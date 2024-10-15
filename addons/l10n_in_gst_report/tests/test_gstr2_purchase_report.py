
from odoo.tests.common import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo import fields


@tagged('post_install', '-at_install')
class GSTR2PurchaseReportTest(AccountTestInvoicingCommon):

    _web_report_ref = 'l10n_in_gst_report.l10n_in_report_gstr_2_purchase_report'

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref='l10n_in.indian_chart_template_standard')

        cls.company_data['company'].write({
            'currency_id': cls.env.ref('base.INR').id,
            'name': 'Indian Test Company',
            'street': 'Sector-5',
            'street2': 'Infocity',
            'state_id': cls.env.ref('base.state_in_gj').id,
            'country_id': cls.env.ref('base.in').id,
            'zip': '382009'
        })
        cls.company_id = cls.company_data['company']
        cls.company_id.partner_id.write({'vat': '12AAAAA1234AAZB', 'l10n_in_gst_treatment': 'regular'})
        cls.env.ref('l10n_in.indian_chart_template_standard')._update_base_tax_grid(cls.company_id)

        # Create Partner
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'partner_a',
            'property_account_receivable_id': cls.company_data['default_account_receivable'].id,
            'property_account_payable_id': cls.company_data['default_account_payable'].id,
            'company_id': False,
            'vat': '24KYXCO5419Y8Z7',
            'l10n_in_gst_treatment': 'regular'
        })

        cls.partner_b = cls.env['res.partner'].create({
            'name': 'partner_b',
            'property_account_receivable_id': cls.company_data['default_account_receivable'].id,
            'property_account_payable_id': cls.company_data['default_account_payable'].id,
            'company_id': False,
            'vat': '16AAAAA1234AAZA',
            'l10n_in_gst_treatment': 'special_economic_zone'
        })

        cls.partner_c = cls.env['res.partner'].create({
            'name': 'partner_c',
            'property_account_receivable_id': cls.company_data['default_account_receivable'].id,
            'property_account_payable_id': cls.company_data['default_account_payable'].id,
            'company_id': False,
            'vat': '12AAAAA8888AAZA',
            'l10n_in_gst_treatment': 'deemed_export'
        })

        cls.web_report = cls.env.ref(cls._web_report_ref, False) if cls._web_report_ref else None

    @classmethod
    def setup_report_data(cls):
        cls.report_options = cls.web_report and cls.web_report._get_options({}) or {}
        cls.report_kwargs = {}
        cls.report_data = cls.get_report_data()
        cls.section_data = cls.report_data.get('sections', [])

    @classmethod
    def get_report_data(cls, context={}, **kwargs):
        return cls.web_report.with_context(**context).with_company(cls.company_id).get_web_report(cls.report_options, **cls.report_kwargs)

    def test_regular_gst_treatment_bill(self):
        tax_id = self.env['account.tax'].search([
            ('type_tax_use', '=', 'purchase'), ('company_id', '=', self.company_id.id), ('amount_type', '=', 'group'),
            ('tax_group_id', '=', self.env.ref('l10n_in.gst_group').id)], limit=1)
        self._create_vendor_bill(move_type='in_invoice', invoice_amount=1000, bill_ref='BILL-101', partner_id=self.partner_a.id, currency_id=self.env.ref('base.INR').id, invoice_date='2024-04-14',
                                 taxes_ids=tax_id.ids, auto_validate=True)
        self.setup_report_data()
        for section in self.section_data:
            self.assertSectionValueEqual(section, 'gst_number', '24KYXCO5419Y8Z7')
            self.assertSectionValueEqual(section, 'customer', 'partner_a')
            self.assertSectionValueEqual(section, 'gst_treatment', 'B2B')
            self.assertSectionValueEqual(section, 'document_type', 'Invoice')
            self.assertSectionValueEqual(section, 'document_number', 'BILL-101')
            self.assertSectionValueEqual(section, 'document_date', fields.Date.to_date('2024-04-14'))
            self.assertSectionValueEqual(section, 'taxable_value', 1000)
            self.assertSectionValueEqual(section, 'total_igst', 0)
            self.assertSectionValueEqual(section, 'total_cgst', 25)
            self.assertSectionValueEqual(section, 'total_sgst', 25)
            self.assertSectionValueEqual(section, 'total_cess', 0)

    def test_special_ecomonic_zone_bill(self):
        tax_id = self.env['account.tax'].search([
            ('type_tax_use', '=', 'purchase'), ('company_id', '=', self.company_id.id), ('amount_type', '=', 'percent'), ('amount', '=', 5),
            ('tax_group_id', '=', self.env.ref('l10n_in.igst_group').id)], limit=1)
        self._create_vendor_bill(move_type='in_invoice', invoice_amount=1000, bill_ref='BILL-102', partner_id=self.partner_b.id, currency_id=self.env.ref('base.INR').id, invoice_date='2024-04-14',
                                 taxes_ids=tax_id.ids, auto_validate=True)
        self.setup_report_data()

        for section in self.section_data:
            self.assertSectionValueEqual(section, 'gst_number', '16AAAAA1234AAZA')
            self.assertSectionValueEqual(section, 'customer', 'partner_b')
            self.assertSectionValueEqual(section, 'gst_treatment', 'SEZWOP')
            self.assertSectionValueEqual(section, 'document_type', 'Invoice')
            self.assertSectionValueEqual(section, 'document_number', 'BILL-102')
            self.assertSectionValueEqual(section, 'document_date', fields.Date.to_date('2024-04-14'))
            self.assertSectionValueEqual(section, 'taxable_value', 1000)
            self.assertSectionValueEqual(section, 'total_igst', 50)
            self.assertSectionValueEqual(section, 'total_cgst', 0)
            self.assertSectionValueEqual(section, 'total_sgst', 0)
            self.assertSectionValueEqual(section, 'total_cess', 0)

    def test_deemed_export_bill(self):
        igst_tax_id = self.env['account.tax'].search([
            ('type_tax_use', '=', 'purchase'), ('company_id', '=', self.company_id.id), ('amount_type', '=', 'percent'), ('amount', '=', 5),
            ('tax_group_id', '=', self.env.ref('l10n_in.igst_group').id)], limit=1)
        cess_tax_id = self.env['account.tax'].search([
            ('type_tax_use', '=', 'purchase'), ('company_id', '=', self.company_id.id), ('amount_type', '=', 'code'), ('name', '=', 'CESS 21% or 4.170'),
            ('tax_group_id', '=', self.env.ref('l10n_in.cess_group').id)], limit=1)
        self._create_vendor_bill(move_type='in_invoice', invoice_amount=1000, bill_ref='BILL-103', partner_id=self.partner_c.id, currency_id=self.env.ref('base.INR').id, invoice_date='2024-04-14',
                                 taxes_ids=(igst_tax_id + cess_tax_id).ids, auto_validate=True)
        self.setup_report_data()

        for section in self.section_data:
            self.assertSectionValueEqual(section, 'gst_number', '12AAAAA8888AAZA')
            self.assertSectionValueEqual(section, 'customer', 'partner_c')
            self.assertSectionValueEqual(section, 'gst_treatment', 'DE')
            self.assertSectionValueEqual(section, 'document_type', 'Invoice')
            self.assertSectionValueEqual(section, 'document_number', 'BILL-103')
            self.assertSectionValueEqual(section, 'document_date', fields.Date.to_date('2024-04-14'))
            self.assertSectionValueEqual(section, 'taxable_value', 1000)
            self.assertSectionValueEqual(section, 'total_igst', 50)
            self.assertSectionValueEqual(section, 'total_cgst', 0)
            self.assertSectionValueEqual(section, 'total_sgst', 0)
            self.assertSectionValueEqual(section, 'total_cess', 210)

    def test_regular_gst_treatment_refund_bill(self):
        tax_id = self.env['account.tax'].search([
            ('type_tax_use', '=', 'purchase'), ('company_id', '=', self.company_id.id), ('amount_type', '=', 'group'),
            ('tax_group_id', '=', self.env.ref('l10n_in.gst_group').id)], limit=1)
        self._create_vendor_bill(move_type='in_refund', invoice_amount=1000, bill_ref='BILL-104', partner_id=self.partner_a.id, currency_id=self.env.ref('base.INR').id, invoice_date='2024-04-14',
                                 taxes_ids=tax_id.ids, auto_validate=True)
        self.setup_report_data()

        for section in self.section_data:
            self.assertSectionValueEqual(section, 'gst_number', '24KYXCO5419Y8Z7')
            self.assertSectionValueEqual(section, 'customer', 'partner_a')
            self.assertSectionValueEqual(section, 'gst_treatment', 'B2B')
            self.assertSectionValueEqual(section, 'document_type', 'Credit Note')
            self.assertSectionValueEqual(section, 'document_number', 'BILL-104')
            self.assertSectionValueEqual(section, 'document_date', fields.Date.to_date('2024-04-14'))
            self.assertSectionValueEqual(section, 'taxable_value', 1000)
            self.assertSectionValueEqual(section, 'total_igst', 0)
            self.assertSectionValueEqual(section, 'total_cgst', 25)
            self.assertSectionValueEqual(section, 'total_sgst', 25)
            self.assertSectionValueEqual(section, 'total_cess', 0)

    def assertSectionValueEqual(self, section, value_key, value_to_check, message=None, **kwargs):
        value_key_name = f'{value_key}_original'
        section_value = section.get('values', {}).get('main_group').get(value_key_name, False)
        self.assertEqual(section_value, value_to_check, message or '')

    def _create_vendor_bill(self, move_type, invoice_amount, bill_ref=False, partner_id=False, currency_id=False, invoice_date=False, quantity=1, taxes_ids=[], auto_validate=False):
        move = self.env['account.move'].with_company(self.company_id).create({
            'move_type': move_type,
            'date': invoice_date or '2024-01-01',
            'invoice_date': invoice_date or '2024-01-01',
            'partner_id': partner_id,
            'currency_id': currency_id or self.company_data['currency'],
            'ref': bill_ref,
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Product 1',
                    'quantity': quantity,
                    'account_id': self.company_data['default_account_expense'].id,
                    'tax_ids': [(6, 0, taxes_ids)],
                    'price_unit': invoice_amount,
                }),
            ]
        })
        if auto_validate:
            move.action_post()
        return move
