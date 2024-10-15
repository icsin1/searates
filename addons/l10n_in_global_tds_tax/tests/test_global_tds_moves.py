
from odoo.tests.common import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class GlobalTDSTaxTest(AccountTestInvoicingCommon):

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
            'zip': '382015'
        })
        cls.company_id = cls.company_data['company']

    def test_create_vendor_bill(self):
        bill_move_id = self._create_vendor_bill(move_type='in_invoice', invoice_amount=1000, bill_ref='BILL-101', partner_id=self.partner_a.id, currency_id=self.env.ref('base.INR').id,
                                                invoice_date='2024-06-06', taxes_ids=[], auto_validate=False)

        # Apply TDS
        self.apply_global_tds_tax(bill_move_id)
        # Confirm Vendor Bill
        bill_move_id.action_post()
        self.assertEqual(bill_move_id.state, 'posted')
        # Create TDS Tax Entry and reconcile
        self.create_global_tds_tax_entry(bill_move_id)

    def test_create_refund_vendor_bill(self):
        bill_move_id = self._create_vendor_bill(move_type='in_refund', invoice_amount=1000, bill_ref='REF-BILL-101', partner_id=self.partner_a.id, currency_id=self.env.ref('base.INR').id,
                                                invoice_date='2024-06-06', taxes_ids=[], auto_validate=False)

        # Apply TDS
        self.apply_global_tds_tax(bill_move_id)
        # Confirm Vendor Bill
        bill_move_id.action_post()
        self.assertEqual(bill_move_id.state, 'posted')
        # Create TDS Tax Entry and reconcile
        self.create_global_tds_tax_entry(bill_move_id)

    def test_reset_to_draft_vendor_bill(self):
        bill_move_id = self._create_vendor_bill(move_type='in_refund', invoice_amount=1000, bill_ref='REF-BILL-101', partner_id=self.partner_a.id, currency_id=self.env.ref('base.INR').id,
                                                invoice_date='2024-06-06', taxes_ids=[], auto_validate=False)

        # Apply TDS
        self.apply_global_tds_tax(bill_move_id)
        self.assertTrue(bill_move_id.tds_tax_id)

        # Confirm Vendor Bill
        bill_move_id.action_post()
        self.assertEqual(bill_move_id.state, 'posted')

        # Create TDS Tax Entry and reconcile
        self.create_global_tds_tax_entry(bill_move_id)
        reversal_move_id = bill_move_id.tds_tax_misc_move_id

        # Reset to Draft and reverse the TDS misc journal entry
        bill_move_id.reset_button_draft()
        self.assertEqual(bill_move_id.state, 'draft')
        self.assertEqual(bill_move_id.tds_tax_misc_move_id, self.env['account.move'])
        self.assertTrue(reversal_move_id.reversal_move_id)

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

    def apply_global_tds_tax(self, move_id):
        tds_tax_id = self.env['account.tax'].search([('type_tax_use', '=', 'purchase'), ('company_id', '=', self.company_id.id), ('tax_group_id', '=', self.env.ref('l10n_in_tds_tcs.tds_group').id)],
                                                    limit=1)
        wizard_rec_id = self.env['wizard.account.global.tds.tax'].with_context(default_account_move_id=move_id.id).create({'tds_tax_id': tds_tax_id.id})
        self.assertEqual(wizard_rec_id.account_move_id, move_id)
        self.assertEqual(wizard_rec_id.tds_tax_id, tds_tax_id)
        wizard_rec_id.action_apply_tds_on_moves()

    def create_global_tds_tax_entry(self, move_id):
        move_id.action_create_global_tds_tax_entry()
        self.assertTrue(move_id.tds_tax_misc_move_id)
        self.assertEqual(move_id.tds_tax_misc_move_id.state, 'posted')
        self.assertEqual(move_id.tds_tax_misc_move_id.amount_total, move_id.global_tds_tax_total_amount)
        self.assertEqual(move_id.payment_state, 'partial')
        self.assertTrue(move_id.tds_tax_misc_move_id.has_reconciled_entries)
