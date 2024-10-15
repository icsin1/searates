# -*- coding: utf-8 -*-

from odoo import models, fields


class ChangeReason(models.Model):
    _name = "change.reason"
    _description = "Quotation State Change Reason"

    name = fields.Char(string='Reasons')
    active = fields.Boolean(string='Active', default=True)
