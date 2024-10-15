# -*- coding: utf-8 -*-
from odoo import models, fields


class MailActivityMixin(models.AbstractModel):
    _inherit = 'mail.activity.mixin'

    activity_user_id = fields.Many2one('res.users', 'Activity Responsible User')
