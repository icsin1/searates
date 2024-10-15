import time
from odoo.tests.common import TransactionCase


class ICSAccountTestCommon(TransactionCase):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super(ICSAccountTestCommon, cls).setUpClass()

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
            'name': 'Because I am accountman!',
            'login': 'accountman',
            'password': 'accountman',
            'groups_id': [(6, 0, cls.env.user.groups_id.ids), (4, cls.env.ref('account.group_account_user').id)],
        })
        user.partner_id.email = 'accountman@test.com'

        # Shadow the current environment/cursor with one having the report user.
        # This is mandatory to test access rights.
        cls.env = cls.env(user=user)
        cls.cr = cls.env.cr

        cls.company_data = cls.setup_company_data('company_1_data', chart_template=chart_template, currency_id=cls.env.ref('base.AED').id)

        user.write({
            'company_ids': [(6, 0, (cls.company_data['company']).ids)],
            'company_id': cls.company_data['company'].id,
        })

        cls.currency_aed = cls.setup_multi_currency_data(cls.env.ref('base.AED'), {}, 1)
        cls.currency_usd = cls.setup_multi_currency_data(cls.env.ref('base.USD'), {}, 3.685)
        cls.currency_eur = cls.setup_multi_currency_data(cls.env.ref('base.EUR'), {}, 3.98)
        cls.currency_inr = cls.setup_multi_currency_data(cls.env.ref('base.INR'), {}, 23)

        # ==== Partners ====
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'partner_a',
            'property_account_receivable_id': cls.company_data['default_account_receivable'].id,
            'property_account_payable_id': cls.company_data['default_account_payable'].id,
            'company_id': False,
        })

        # ==== Payment methods ====
        bank_journal = cls.company_data['default_journal_bank']

        cls.inbound_payment_method_line = bank_journal.inbound_payment_method_line_ids[0]
        cls.outbound_payment_method_line = bank_journal.outbound_payment_method_line_ids[0]

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
    def setup_multi_currency_data(cls, currency, default_values=None, fixed_rate=3.0):
        default_values = default_values or {}

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

    def _create_invoice(self, move_type='out_invoice', invoice_amount=50, partner_id=None, currency_id=None, date_invoice=None, payment_term_id=False, auto_validate=False, **kwargs):
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

        invoice = self.env['account.move'].sudo().with_context(default_move_type=move_type).create(invoice_vals)
        if auto_validate:
            invoice.action_post()
        return invoice

    def create_invoice(self, move_type='out_invoice', invoice_amount=50, currency_id=None, **kwargs):
        return self._create_invoice(move_type=move_type, invoice_amount=invoice_amount, currency_id=currency_id, auto_validate=True, **kwargs)

    def create_payment(self, payment_amount, payment_currency, payment_date=None, partner=None, payment_type='inbound', auto_post=False):
        payment = self.env['account.payment'].create({
            'amount': payment_amount,
            'date': payment_date or time.strftime('%Y') + '-07-02',
            'currency_id': payment_currency.id,
            'payment_type': payment_type,
            'partner_type': 'customer' if payment_type == 'inbound' else 'supplier',
            'partner_id': partner and partner.id or self.partner_a.id
        })
        if auto_post:
            payment.action_post()
        return payment

    def register_payment(self, invoice, payment_amount, payment_date, payment_currency=None, auto_post=False):
        payment = self.env['account.payment.register'].with_context(active_model=invoice._name, active_ids=invoice.ids)
        payment.create({
            'payment_date': payment_date,
            'amount': payment_amount,
            'currency_id': payment_currency and payment_currency.id or invoice.currency_id.id,
            'payment_method_line_id': self.inbound_payment_method_line.id,
        })._create_payments()

    @classmethod
    def create_partner(cls, values):
        partner = cls.env['res.partner'].create({
            'property_account_receivable_id': cls.company_data['default_account_receivable'].id,
            'property_account_payable_id': cls.company_data['default_account_payable'].id,
            **values
        })
        partner._compute_commercial_partner()
        return partner


class PaymentAdjustmentCommon(ICSAccountTestCommon):

    def _amount_to_home_currency(self, amount, company, from_currency, date):
        return self._amount_to_currency(amount, company, from_currency, company.currency_id, date)

    def _amount_to_currency(self, amount, company, from_currency, to_currency, date):
        return from_currency._convert(amount, to_currency, company, date)

    def _validate_payment_adjustment(self, invoice_data, payment_data, result_data, move_type='out_invoice'):
        """ Single invoice and payment adjustment Testing
        """

        # Creating Invoice and Validating
        invoice_amount = invoice_data.get('invoice_amount')
        invoice_currency = invoice_data.get('invoice_currency')
        invoice = self.create_invoice(move_type=move_type, invoice_amount=invoice_amount, currency_id=invoice_currency.get('currency').id)
        self.assertEqual(invoice.currency_id, invoice_currency.get('currency'), 'Invoice currency must be in {}'.format(invoice_currency.get('currency').name))
        self.assertEqual(invoice.state, 'posted', 'Invoice must be posted')
        for move_line in invoice.line_ids:
            amount_home_currency = self._amount_to_home_currency(invoice_amount, invoice.company_id, invoice_currency.get('currency'), invoice.date)
            if move_line.account_id.user_type_id.internal_group == 'income':
                self.assertEqual(move_line.credit, amount_home_currency, 'Invoice Line Credit amount in local currency must match')
            if move_line.account_id.user_type_id.internal_group == 'asset':
                self.assertEqual(move_line.debit, amount_home_currency, 'Invoice Line Debit amount in local currency must match')

        # Creating new payment and validating
        payment_amount = payment_data.get('payment_amount')
        payment_currency = payment_data.get('payment_currency')
        payment = self.create_payment(payment_amount, payment_currency.get("currency"), auto_post=True, payment_type='inbound' if move_type == 'out_invoice' else 'outbound')

        self.assertEqual(payment.currency_id, payment_currency.get('currency'), 'Payment currency must be in {}'.format(payment_currency.get('currency').name))
        payment_in_home_currency = self._amount_to_home_currency(payment_amount, payment.company_id, payment_currency.get('currency'), payment.date)
        for payment_line in payment.line_ids:
            if payment_line.debit:
                self.assertEqual(payment_line.debit, payment_in_home_currency, 'Payment Line Debit amount in local currency must match')
            if payment_line.credit:
                self.assertEqual(payment_line.credit, payment_in_home_currency, 'Payment Line Credit amount in local currency must match')

        # Adjusting payment to invoice
        payment_wizard_context = payment.action_adjust_payment().get('context', {})
        wizard = self.env['adjust.payment.wizard'].with_context(**payment_wizard_context).create({})

        self.assertEqual(len(wizard.line_ids), 1, 'Wizard should contain only single invoice')
        self.assertEqual(wizard.line_ids.move_id.name, invoice.name, 'Adjustment wizard invoice must be same as pending to adjust')
        self.assertEqual(wizard.line_ids.amount_total, self._amount_to_currency(invoice_amount, invoice.company_id, invoice_currency.get('currency'), payment_currency.get('currency'), invoice.date),
                         'Adjustment line total amount must match with payment amount in {}'.format(payment_currency.get('currency').name))
        self.assertEqual(wizard.line_ids.amount_total_signed, self._amount_to_home_currency(invoice_amount, invoice.company_id, invoice_currency.get('currency'), invoice.date),
                         'Adjustment line total signed amount must match with payment converted amount in {}'.format(invoice.company_id.currency_id.name))

        # Selecting line and adjusting full amount
        wizard.line_ids.is_checked = True
        if payment_data.get('payment_adjust_amount'):
            wizard.line_ids.amount_residual_signed = payment_data.get('payment_adjust_amount')
            self.assertEqual(wizard.line_ids.amount_residual_signed, result_data.get('adjustment_amount'), 'Setting Adjustment amount as partial amount in AED')
        else:
            wizard.line_ids.amount_residual_signed = result_data.get('adjustment_amount')
            self.assertEqual(wizard.line_ids.amount_residual_signed, result_data.get('adjustment_amount'), 'Setting Adjustment amount as partial amount in AED')

        # Adjusting amount
        self.assertEqual(invoice.amount_residual, invoice_amount, 'Before adjustment due is {} {}'.format(invoice_amount, invoice_currency.get('currency').name))
        wizard.action_adjust_payment()

        invoice_currency_adjusted = self._amount_to_currency(result_data.get('adjustment_amount'), invoice.company_id, invoice.company_id.currency_id, invoice.currency_id, invoice.date)
        invoice_residual = invoice_amount - invoice_currency_adjusted

        self.assertEqual(invoice.amount_residual, round(invoice_residual, 2), 'After adjustment due is {} {}'.format(round(invoice_residual, 2), invoice.currency_id.name))
        self.assertEqual(invoice.payment_state, result_data.get('invoice_payment_status'), 'Invoice payment status must be {}'.format(result_data.get('invoice_payment_status')))

        # Recomputing remaining amount
        payment._compute_total_remaining_amount()
        payment_amount_adjusted = self._amount_to_currency(result_data.get('adjustment_amount'), invoice.company_id, invoice.company_id.currency_id, payment.currency_id, payment.date)
        payment_remaining_amount = self._amount_to_home_currency(payment_amount - payment_amount_adjusted, invoice.company_id, payment.currency_id, payment.date)
        self.assertEqual(round(payment.total_remaining_amount, 2), round(payment_remaining_amount, 2),
                         'After adjustment payment remaining amount need to be {} AED'.format(round(payment_remaining_amount, 2)))

        # Matched Entries to validate
        matched_lines = invoice.line_ids.filtered(lambda line: line.account_id.user_type_id.internal_group == ('asset' if invoice.move_type == 'out_invoice' else 'liability'))
        matched_lines = matched_lines.matched_credit_ids if invoice.move_type == 'out_invoice' else matched_lines.matched_debit_ids
        self.assertEqual(len(matched_lines), 1, 'Matched Line must be 1')

        if invoice.move_type == 'out_invoice':
            # Debit move must be Invoice
            self.assertEqual(matched_lines.debit_move_id.move_id, invoice, 'Matched Line debit move must be Invoice')
            self.assertEqual(matched_lines.debit_currency_id, invoice_currency.get('currency'), 'Matched Line debit currency must same as Invoice Currency')
            self.assertEqual(matched_lines.debit_amount_currency, invoice_currency_adjusted, 'Matched Line debit currency must be {} {}'.format(invoice_currency_adjusted, invoice.currency_id.name))

            # Credit move must be Payment line
            self.assertEqual(matched_lines.credit_move_id.move_id.payment_id, payment, 'Matched Line credit move must be payment')
            self.assertEqual(matched_lines.credit_currency_id, payment_currency.get('currency'), 'Matched Line Credit currency must be {}'.format(payment.currency_id.name))
            self.assertEqual(matched_lines.credit_amount_currency, payment_amount_adjusted, 'Matched Line credit currency must be {} {}'.format(payment_amount_adjusted, payment.currency_id.name))
        elif invoice.move_type == 'in_invoice':
            # Debit move must be Payment
            self.assertEqual(matched_lines.debit_move_id.move_id.payment_id, payment, 'Matched Line Debit move must be payment')
            self.assertEqual(matched_lines.debit_currency_id, payment_currency.get('currency'), 'Matched Line Debit currency must be {}'.format(payment.currency_id.name))
            self.assertEqual(matched_lines.debit_amount_currency, payment_amount_adjusted, 'Matched Line Debit currency must be {} {}'.format(payment_amount_adjusted, payment.currency_id.name))

            # Credit move must be Bill
            self.assertEqual(matched_lines.credit_move_id.move_id, invoice, 'Matched Line credit move must be Bill')
            self.assertEqual(matched_lines.credit_currency_id, invoice_currency.get('currency'), 'Matched Line credit currency must same as Bill Currency')
            self.assertEqual(matched_lines.credit_amount_currency, invoice_currency_adjusted, 'Matched Line credit currency must be {} {}'.format(invoice_currency_adjusted, invoice.currency_id.name))

        # Company currency amount
        self.assertEqual(matched_lines.company_currency_id, self.currency_aed.get('currency'), 'Matched Line company currency must be AED')
        self.assertEqual(matched_lines.amount, result_data.get('adjustment_amount'), 'Matched Line company currency amount be {} AED'.format(result_data.get('adjustment_amount')))

    def _validate_multi_invoice_payment_adjustment(self, invoices_data, payment_data, move_type='out_invoice'):
        """ Single invoice and payment adjustment Testing
        """
        invoice_details = {}
        # Creating Invoice and Validating
        for invoice_data in invoices_data:
            invoice_amount = invoice_data.get('invoice_amount')
            invoice_currency = invoice_data.get('invoice_currency')
            invoice = self.create_invoice(move_type=move_type, invoice_amount=invoice_amount, currency_id=invoice_currency.get('currency').id)
            self.assertEqual(invoice.currency_id, invoice_currency.get('currency'), 'Invoice currency must be in {}'.format(invoice_currency.get('currency').name))
            self.assertEqual(invoice.state, 'posted', 'Invoice must be posted')
            for move_line in invoice.line_ids:
                amount_home_currency = self._amount_to_home_currency(invoice_amount, invoice.company_id, invoice_currency.get('currency'), invoice.date)
                if move_line.account_id.user_type_id.internal_group == 'income':
                    self.assertEqual(move_line.credit, amount_home_currency, 'Invoice Line Credit amount in local currency must match')
                if move_line.account_id.user_type_id.internal_group == 'asset':
                    self.assertEqual(move_line.debit, amount_home_currency, 'Invoice Line Debit amount in local currency must match')
            invoice_details.update({invoice: invoice_data})

        # Creating new payment and validating
        payment_amount = payment_data.get('payment_amount')
        payment_currency = payment_data.get('payment_currency')
        payment = self.create_payment(payment_amount, payment_currency.get("currency"), auto_post=True, payment_type='inbound' if move_type == 'out_invoice' else 'outbound')

        self.assertEqual(payment.currency_id, payment_currency.get('currency'), 'Payment currency must be in {}'.format(payment_currency.get('currency').name))
        payment_in_home_currency = self._amount_to_home_currency(payment_amount, payment.company_id, payment_currency.get('currency'), payment.date)
        for payment_line in payment.line_ids:
            if payment_line.debit:
                self.assertEqual(payment_line.debit, payment_in_home_currency, 'Payment Line Debit amount in local currency must match')
            if payment_line.credit:
                self.assertEqual(payment_line.credit, payment_in_home_currency, 'Payment Line Credit amount in local currency must match')

        # Adjusting payment to invoice
        payment_wizard_context = payment.action_adjust_payment().get('context', {})
        wizard = self.env['adjust.payment.wizard'].with_context(**payment_wizard_context).create({})

        self.assertEqual(len(wizard.line_ids), len(invoices_data), 'Wizard should contain {} invoice'.format(len(invoices_data)))
        for invoice, inv_data in invoice_details.items():
            invoice_amount = inv_data.get('invoice_amount')
            invoice_currency = inv_data.get('invoice_currency')
            wizard_line = wizard.line_ids.filtered(lambda wl: wl.move_id == invoice)
            self.assertEqual(wizard_line.move_id.name, invoice.name, 'Adjustment wizard invoice must be same as pending to adjust')
            inv_amount_total = self._amount_to_currency(invoice_amount, invoice.company_id, invoice_currency.get('currency'), payment_currency.get('currency'), invoice.date)
            self.assertEqual(wizard_line.amount_total, inv_amount_total, 'Adjustment line total amount must match with payment amount in {}'.format(payment_currency.get('currency').name))
            self.assertEqual(wizard_line.amount_total_signed, self._amount_to_home_currency(invoice_amount, invoice.company_id, invoice_currency.get('currency'), invoice.date),
                             'Adjustment line total signed amount must match with payment converted amount in {}'.format(invoice.company_id.currency_id.name))

            # Selecting line and adjusting amount
            wizard_line.is_checked = True
            wizard_line.amount_residual_signed = inv_data.get('adjustment_amount')
            self.assertEqual(wizard_line.amount_residual_signed, inv_data.get('adjustment_amount'), 'Setting Adjustment amount as partial amount in AED')

            # Adjusting amount
            self.assertEqual(invoice.amount_residual, invoice_amount, 'Before adjustment due is {} {}'.format(invoice_amount, invoice_currency.get('currency').name))

        wizard.action_adjust_payment()

        total_payment_amount_adjusted = 0
        for invoice, inv_data in invoice_details.items():
            invoice_amount = inv_data.get('invoice_amount')
            invoice_currency = inv_data.get('invoice_currency')
            wizard_line = wizard.line_ids.filtered(lambda wl: wl.move_id == invoice)

            invoice_currency_adjusted = self._amount_to_currency(inv_data.get('adjustment_amount'), invoice.company_id, invoice.company_id.currency_id, invoice.currency_id, invoice.date)
            invoice_residual = invoice_amount - invoice_currency_adjusted

            self.assertEqual(invoice.amount_residual, round(invoice_residual, 2), 'After adjustment due is {} {}'.format(round(invoice_residual, 2), invoice.currency_id.name))
            self.assertEqual(invoice.payment_state, inv_data.get('invoice_payment_status'), 'Invoice payment status must be {}'.format(inv_data.get('invoice_payment_status')))

            total_payment_amount_adjusted += self._amount_to_currency(inv_data.get('adjustment_amount'), invoice.company_id, invoice.company_id.currency_id, payment.currency_id, payment.date)

        # Recomputing remaining amount
        payment._compute_total_remaining_amount()
        payment_remaining_amount = self._amount_to_home_currency(payment_amount - total_payment_amount_adjusted, payment.company_id, payment.currency_id, payment.date)
        self.assertEqual(round(payment.total_remaining_amount, 2), round(payment_remaining_amount, 2), 'After adjustment payment remaining amount need to be {} AED'.format(
            round(payment_remaining_amount, 2)
        ))

        for invoice, inv_data in invoice_details.items():
            invoice_amount = inv_data.get('invoice_amount')
            invoice_currency = inv_data.get('invoice_currency')
            payment_amount_adjusted = self._amount_to_currency(inv_data.get('adjustment_amount'), invoice.company_id, invoice.company_id.currency_id, payment.currency_id, payment.date)
            invoice_currency_adjusted = self._amount_to_currency(inv_data.get('adjustment_amount'), invoice.company_id, invoice.company_id.currency_id, invoice.currency_id, invoice.date)

            # Matched Entries to validate
            matched_lines = invoice.line_ids.filtered(lambda line: line.account_id.user_type_id.internal_group == ('asset' if invoice.move_type == 'out_invoice' else 'liability'))
            matched_lines = matched_lines.matched_credit_ids if invoice.move_type == 'out_invoice' else matched_lines.matched_debit_ids
            self.assertEqual(len(matched_lines), 1, 'Matched Line must be 1')

            if invoice.move_type == 'out_invoice':
                # Debit move must be Invoice
                self.assertEqual(matched_lines.debit_move_id.move_id, invoice, 'Matched Line debit move must be Invoice')
                self.assertEqual(matched_lines.debit_currency_id, invoice_currency.get('currency'), 'Matched Line debit currency must same as Invoice Currency')
                self.assertEqual(matched_lines.debit_amount_currency, invoice_currency_adjusted, 'Matched Line debit currency must be {} {}'.format(
                    invoice_currency_adjusted, invoice.currency_id.name
                ))

                # Credit move must be Payment line
                self.assertEqual(matched_lines.credit_move_id.move_id.payment_id, payment, 'Matched Line credit move must be payment')
                self.assertEqual(matched_lines.credit_currency_id, payment_currency.get('currency'), 'Matched Line Credit currency must be {}'.format(payment.currency_id.name))
                self.assertEqual(matched_lines.credit_amount_currency, payment_amount_adjusted, 'Matched Line credit currency must be {} {}'.format(payment_amount_adjusted, payment.currency_id.name))
            elif invoice.move_type == 'in_invoice':
                # Debit move must be Payment
                self.assertEqual(matched_lines.debit_move_id.move_id.payment_id, payment, 'Matched Line Debit move must be payment')
                self.assertEqual(matched_lines.debit_currency_id, payment_currency.get('currency'), 'Matched Line Debit currency must be {}'.format(payment.currency_id.name))
                self.assertEqual(matched_lines.debit_amount_currency, payment_amount_adjusted, 'Matched Line Debit currency must be {} {}'.format(payment_amount_adjusted, payment.currency_id.name))

                # Credit move must be Bill
                self.assertEqual(matched_lines.credit_move_id.move_id, invoice, 'Matched Line credit move must be Bill')
                self.assertEqual(matched_lines.credit_currency_id, invoice_currency.get('currency'), 'Matched Line credit currency must same as Bill Currency')
                self.assertEqual(matched_lines.credit_amount_currency, invoice_currency_adjusted,
                                 'Matched Line credit currency must be {} {}'.format(invoice_currency_adjusted, invoice.currency_id.name))

            # Company currency amount
            self.assertEqual(matched_lines.company_currency_id, self.currency_aed.get('currency'), 'Matched Line company currency must be AED')
            self.assertEqual(matched_lines.amount, inv_data.get('adjustment_amount'), 'Matched Line company currency amount be {} AED'.format(inv_data.get('adjustment_amount')))
