from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    currency_exchange_rate = fields.Float('Ex.Rate', copy=False, digits='Currency Exchange Rate')
    charge_rate_per_unit = fields.Float('Amount/Qty', copy=False, digits='Product Price')

    def copy_data(self, default=None):
        res = super(AccountMoveLine, self).copy_data(default=default)
        if 'move_reverse_cancel' in self.env.context:
            for line, values in zip(self, res):
                values.update({
                    'currency_exchange_rate': line.currency_exchange_rate,
                    'charge_rate_per_unit': line.charge_rate_per_unit
                })
        return res

    def get_report_label_name(self):
        label = self.move_id.label if self.move_id.move_type != 'entry' else self.name
        return label or ''
