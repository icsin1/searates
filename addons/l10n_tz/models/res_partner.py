# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_tz_tin = fields.Char('TIN', copy=False)
