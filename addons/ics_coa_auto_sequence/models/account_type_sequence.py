
from odoo import models, fields


class account_type_sequence(models.Model):
    _name = 'account.type.sequence'
    _description = "Account Type Sequence"
    _rec_name = 'code'

    code = fields.Char(required=True, copy=False)
    account_type_id = fields.Many2one('account.account.type', required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    next_no = fields.Integer(default=1, copy=False)

    _sql_constraints = [
        ('account_type_company_uniq', 'unique (account_type_id, company_id)', 'The account type sequence must be unique per company !')
    ]
