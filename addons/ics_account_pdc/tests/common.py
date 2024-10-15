import time

from odoo import fields
from odoo.tests.common import TransactionCase


class ICSAccountPDCTestCommon(TransactionCase):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super(ICSAccountPDCTestCommon, cls).setUpClass()

        assert 'post_install' in cls.test_tags, 'This test requires a CoA to be installed, it should be tagged "post_install"'

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
            'name': 'PDC Payment Test',
            'login': 'pdc_test',
            'password': 'pdc_test',
            'groups_id': [(6, 0, cls.env.user.groups_id.ids), (4, cls.env.ref('account.group_account_user').id)],
        })
        user.partner_id.email = 'pdc@test.com'

        # Shadow the current environment/cursor with one having the report user.
        # This is mandatory to test access rights.
        cls.env = cls.env(user=user)
        cls.cr = cls.env.cr

        cls.company_data = cls.setup_company_data('company_1_data', chart_template=chart_template, currency_id=cls.env.ref('base.AED').id)

        user.write({
            'company_ids': [(6, 0, (cls.company_data['company']).ids)],
            'company_id': cls.company_data['company'].id,
        })

        cls.currency_aed = cls.setup_multi_currency_data(cls.env.ref('base.AED'), 1)
        cls.currency_usd = cls.setup_multi_currency_data(cls.env.ref('base.USD'), 3.685)
        cls.currency_eur = cls.setup_multi_currency_data(cls.env.ref('base.EUR'), 3.98)
        cls.currency_inr = cls.setup_multi_currency_data(cls.env.ref('base.INR'), 23)

        # ==== Partners ====
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'pdc_partner',
            'property_account_receivable_id': cls.company_data['default_account_receivable'].id,
            'property_account_payable_id': cls.company_data['default_account_payable'].id,
            'company_id': False,
        })

        # ==== Payment methods ====
        bank_journal = cls.company_data['default_journal_bank']

        cls.inbound_payment_method_line = bank_journal.inbound_payment_method_line_ids.filtered(lambda pml: pml.payment_method_id.code == "pdc")[0]
        cls.outbound_payment_method_line = bank_journal.outbound_payment_method_line_ids.filtered(lambda pml: pml.payment_method_id.code == "pdc")[0]

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):

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
        cls.env.user.company_ids |= company

        chart_template.try_loading(company=company, install_demo=False)

        # The currency could be different after the installation of the chart template.
        if kwargs.get('currency_id'):
            company.write({'currency_id': kwargs['currency_id']})

        default_journal_bank = cls.env['account.journal'].search([
            ('company_id', '=', company.id), ('type', '=', 'bank')], limit=1)
        cls.assertTrue(company.pdc_receivable_account_id, 'PDC Receivable account must be created!')
        cls.assertTrue(company.pdc_payable_account_id, 'PDC Receivable account must be created!')
        cls.pdc_receivable_account_id = company.pdc_receivable_account_id
        cls.pdc_payable_account_id = company.pdc_payable_account_id
        cls.env['account.payment.method.line'].create({
            'payment_method_id': cls.env.ref('ics_account_pdc.account_payment_method_pdc_out').id,
            'payment_account_id': cls.pdc_receivable_account_id.id,
            'journal_id': default_journal_bank.id,
        })
        cls.env['account.payment.method.line'].create({
            'payment_method_id': cls.env.ref('ics_account_pdc.account_payment_method_pdc_in').id,
            'payment_account_id': cls.pdc_payable_account_id.id,
            'journal_id': default_journal_bank.id,
        })
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
            'default_account_tax_purchase': company.account_purchase_tax_id.mapped('invoice_repartition_line_ids.account_id'),
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
            'default_journal_bank': default_journal_bank,
            'default_journal_cash': cls.env['account.journal'].search([
                    ('company_id', '=', company.id),
                    ('type', '=', 'cash')
                ], limit=1),
            'default_tax_sale': company.account_sale_tax_id,
            'default_tax_purchase': company.account_purchase_tax_id,
        }

    @classmethod
    def setup_multi_currency_data(cls, currency, fixed_rate=3.0):
        currency.write({
            'is_fixed_rate_currency': True,
            'fixed_rate': fixed_rate,
            'active': True
        })
        return {
            'currency': currency,
            'rate': currency.rate,
            'fixed_rate': fixed_rate
        }

    def _create_invoice(self, move_type='out_invoice', invoice_amount=50, partner_id=None, currency_id=None, date_invoice=None, auto_validate=False):
        date_invoice = date_invoice or time.strftime('%Y') + '-07-01'

        invoice_vals = {
            'move_type': move_type,
            'partner_id': partner_id or self.partner_a,
            'invoice_date': date_invoice,
            'date': date_invoice,
            'invoice_line_ids': [(0, 0, {
                'name': 'product that cost %s' % invoice_amount,
                'quantity': 1,
                'price_unit': invoice_amount,
                'tax_ids': [(6, 0, [])],
            })]
        }

        if currency_id:
            invoice_vals['currency_id'] = currency_id

        invoice = self.env['account.move'].with_context(default_move_type=move_type).create(invoice_vals)
        if auto_validate:
            invoice.sudo().action_post()
        return invoice

    def create_invoice(self, move_type='out_invoice', invoice_amount=50, currency_id=None):
        return self._create_invoice(move_type=move_type, invoice_amount=invoice_amount, currency_id=currency_id, auto_validate=True)

    def create_payment(self, payment_amount, payment_currency, payment_type='inbound', auto_post=False):
        payment = self.env['account.payment'].create({
            'amount': payment_amount,
            'date': time.strftime('%Y') + '-07-02',
            'currency_id': payment_currency.id,
            'payment_type': payment_type,
            'partner_type': 'customer' if payment_type == 'inbound' else 'supplier',
            'partner_id': self.partner_a.id,
            'journal_id': self.company_data.get('default_journal_bank').id,
            'payment_method_line_id': self.inbound_payment_method_line.id if payment_type == 'inbound' else self.outbound_payment_method_line.id,
            'cheque_no': '524000',
            'cheque_date': fields.Date.today(),
            'cheque_ref': '000000239',
        })
        if auto_post:
            payment.action_post()
        return payment


class PaymentAdjustmentCommon(ICSAccountPDCTestCommon):

    def _amount_to_home_currency(self, amount, company, from_currency, date):
        return self._amount_to_currency(amount, company, from_currency, company.currency_id, date)

    def _amount_to_currency(self, amount, company, from_currency, to_currency, date):
        return from_currency._convert(amount, to_currency, company, date)

    def _get_invoice(self, invoice_data, move_type='out_invoice'):
        invoice_amount = invoice_data.get('invoice_amount')
        invoice_currency = invoice_data.get('invoice_currency')
        invoice = self.create_invoice(move_type=move_type, invoice_amount=invoice_amount,
                                      currency_id=invoice_currency.get('currency').id)
        return invoice

    def _get_invoice_with_payment(self, invoice_data, payment_data, move_type='out_invoice'):
        invoice = self._get_invoice(invoice_data, move_type=move_type)
        payment_amount = payment_data.get('payment_amount')
        payment_currency = payment_data.get('payment_currency')
        payment = self.create_payment(payment_amount, payment_currency.get("currency"), auto_post=True,
                                      payment_type='inbound' if move_type == 'out_invoice' else 'outbound')
        return invoice, payment

    def _adjust_payment(self, payment, result_data):
        payment_wizard_context = payment.action_adjust_payment().get('context', {})
        wizard = self.env['adjust.payment.wizard'].with_context(**payment_wizard_context).create({})
        # Selecting line and adjusting full amount
        wizard.line_ids.is_checked = True
        wizard.line_ids.amount_residual_signed = result_data.get('adjustment_amount')
        wizard.action_adjust_payment()

    def _pdc_payment_cheque_bounced(self, payment):
        self.assertTrue(payment.pdc_payment_id, 'A PDC Payment Record must be created.')
        pdc_payment_id = payment.pdc_payment_id
        pdc_payment_id.action_mark_deposited()
        self.assertEqual(pdc_payment_id.state, 'deposited', 'PDC Payment must be in Deposited State.')
        pdc_payment_id.action_mark_bounced()
        self.assertEqual(pdc_payment_id.state, 'bounced', 'PDC Payment must be in Bounced State.')
        self.assertTrue(payment.move_id.reversal_move_id, 'Reverse Entry must be created.')

    def _pdc_payment_cheque_returned(self, payment):
        self.assertTrue(payment.pdc_payment_id, 'A PDC Payment Record must be created.')
        pdc_payment_id = payment.pdc_payment_id
        pdc_payment_id.action_mark_deposited()
        self.assertEqual(pdc_payment_id.state, 'deposited', 'PDC Payment must be in Deposited State.')
        pdc_payment_id.action_mark_returned()
        self.assertEqual(pdc_payment_id.state, 'returned', 'PDC Payment must be in Returned State.')
        self.assertTrue(payment.move_id.reversal_move_id, 'Reverse Entry must be created.')

    def _pdc_payment_cheque_done(self, payment):
        self.assertTrue(payment.pdc_payment_id, 'A PDC Payment Record must be created.')
        pdc_payment_id = payment.pdc_payment_id
        pdc_payment_id.action_mark_deposited()
        self.assertEqual(pdc_payment_id.state, 'deposited', 'PDC Payment must be in Deposited State.')
        pdc_payment_id.clearing_date = fields.Date.today()
        pdc_payment_id.action_mark_done()
        self.assertEqual(pdc_payment_id.state, 'done', 'PDC Payment must be in Done State.')
        self.assertTrue(pdc_payment_id.move_id, 'Journal Entry must be created.')
        self.assertEqual(pdc_payment_id.move_id.currency_id, pdc_payment_id.payment_id.move_id.currency_id, 'PDC journal entry and linked payment\'s journal entry must have same currency selected')
        payment_journal_item_debit_sum = sum(pdc_payment_id.payment_id.move_id.mapped('line_ids.debit'))
        pdc_journal_item_debit_sum = sum(pdc_payment_id.move_id.mapped('line_ids.debit'))
        self.assertEqual(payment_journal_item_debit_sum, pdc_journal_item_debit_sum, 'Total of debit amount of PDC payment journal item and linked payment\'s journal item must be equal')
        payment_journal_item_credit_sum = sum(pdc_payment_id.payment_id.move_id.mapped('line_ids.credit'))
        pdc_journal_item_credit_sum = sum(pdc_payment_id.move_id.mapped('line_ids.credit'))
        self.assertEqual(payment_journal_item_credit_sum, pdc_journal_item_credit_sum, 'Total of credit amount of PDC payment journal item and linked payment\'s journal item must be equal')

    def _validate_pdc_payment_adjustment(self, invoice_data, payment_data, result_data, move_type="out_invoice"):
        """ Single invoice and payment adjustment Testing
        """
        # Creating Invoice and Validating
        invoice, payment = self._get_invoice_with_payment(invoice_data, payment_data, move_type=move_type)
        self._adjust_payment(payment, result_data)
        self._pdc_payment_cheque_bounced(payment)
        invoice, payment = self._get_invoice_with_payment(invoice_data, payment_data, move_type=move_type)
        self._adjust_payment(payment, result_data)
        self._pdc_payment_cheque_returned(payment)

    def _register_payment(self, invoice, result_data, move_type='out_invoice'):
        register_payment_wizard = invoice.action_register_payment().get('context', {})
        wizard = self.env['account.payment.register'].with_context(**register_payment_wizard).create({
            'journal_id': self.company_data['default_journal_bank'].id,
            'payment_method_line_id': self.outbound_payment_method_line.id if move_type == 'out_invoice' else self.inbound_payment_method_line.id,
            'amount': result_data.get('adjustment_amount'),
            'cheque_no': '524000',
            'cheque_date': fields.Date.today(),
            'cheque_ref': '000000239',
        })
        payments = wizard._create_payments()
        return payments[0]

    def _validate_pdc_payment_registered(self, invoice_data, result_data, move_type='out_invoice'):
        """ Single invoice and payment adjustment Testing
        """
        # Creating Invoice and Validating
        invoice = self._get_invoice(invoice_data, move_type=move_type)
        payment = self._register_payment(invoice, result_data, move_type=move_type)
        self._pdc_payment_cheque_bounced(payment)
        invoice = self._get_invoice(invoice_data, move_type=move_type)
        payment = self._register_payment(invoice, result_data, move_type=move_type)
        self._pdc_payment_cheque_returned(payment)
        invoice = self._get_invoice(invoice_data, move_type=move_type)
        payment = self._register_payment(invoice, result_data, move_type=move_type)
        self._pdc_payment_cheque_done(payment)
