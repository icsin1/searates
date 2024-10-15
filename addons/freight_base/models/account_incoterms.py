from odoo import api, fields, models

class AccountIncoterms(models.Model):
    _inherit = "account.incoterms"

    incoterm_check = fields.Boolean('Enable Pick-up & Delivery Address')
