from odoo import fields
from odoo.tests import TransactionCase, tagged
from .common import Testtds


# @tagged('-at_install', 'post_install')
class TestAccountTds(TransactionCase):

    # @classmethod
    # def setUp(self):
    #     super(TestTds, self).setUp()

    def test_account_tds(self):
        print('Automation Test case')
        account_move = self.env['account.move'].with_context(tracking_disable=True).create({
            'name' : 'INV/2024/05/0000',
            'compute_tds' : True,
            'total_tds_amount' : 100.00,
            'company_calculate_tds' : self.company_data['calculate_tds'].id,
        })
        account_move.invoice_line_ids.create({
            'account_tds_rate_id' : self.account_tds_rate_id.id
        })
        print('\n\n\nAccount Move', account_move)
        self.assertTrue(account_move)