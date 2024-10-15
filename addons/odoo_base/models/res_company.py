# -*- coding: utf-8 -*-
import pytz
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    logo_1024 = fields.Binary(related='partner_id.image_1024', readonly=False)
    logo_512 = fields.Binary(related='partner_id.image_512', readonly=False)
    logo_256 = fields.Binary(related='partner_id.image_256', readonly=False)
    logo_128 = fields.Binary(related='partner_id.image_128', readonly=False)
    allow_report_print_datetime_log = fields.Boolean(default=False)
    show_settings = fields.Boolean(compute='_compute_show_settings')

    def _compute_show_settings(self):
        for company in self:
            company.show_settings = company.id == self.env.company.id

    def _get_time_log_in_user_tz(self):
        user = self.env.user
        now = fields.Datetime.now()
        # converting time to users timezone
        if user.tz:
            tz = pytz.timezone(user.tz) or pytz.utc
            time = pytz.utc.localize(now).astimezone(tz)
        else:
            time = now
        return time

    def _get_report_footer_print_log(self):
        return "{} - {}".format(self._get_time_log_in_user_tz(), self.env.user.name)

    def allow_print_timestamp(self):
        return self.allow_report_print_datetime_log
