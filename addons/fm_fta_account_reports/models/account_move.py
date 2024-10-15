
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_bank_details(self):
        """ Get Company Bank accounts by currency
            Return list of dictionary of banks by currency.
            """
        # Grouping banks by currency
        banks_by_currency = {}
        banks = self.company_id.bank_ids.filtered(lambda l: l.visible_on_report)
        currencies = banks.mapped('currency_id')
        for currency in currencies:
            currency_banks = banks_by_currency.get(currency, [])
            currency_banks += banks.filtered(lambda bank: bank.currency_id == currency)
            banks_by_currency.update({currency: currency_banks})

        return banks_by_currency
