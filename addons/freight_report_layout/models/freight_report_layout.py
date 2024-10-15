# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.misc import get_lang


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    @api.depends('report_layout_id')
    def _compute_is_sr_custom_layout(self):
        searate_layout = self.env.ref('freight_report_layout.report_layout_searate')
        for rec in self:
            rec.is_sr_custom_layout = True if rec.report_layout_id.id == searate_layout.id else False

    report_logo = fields.Binary(related="company_id.report_logo", readonly=False)
    sr_report_header = fields.Html(related='company_id.sr_report_header', readonly=False)
    is_sr_custom_layout = fields.Boolean(compute='_compute_is_sr_custom_layout')

    @property
    def _current_user(self):
        return self.env.user

    @property
    def _current_date(self):
        lang = get_lang(self.env, self.env.user.lang)
        date_format = lang.date_format
        time_format = lang.time_format
        datetime_format = date_format + " " + time_format
        return fields.Datetime.context_timestamp(self, fields.Datetime.now()).strftime(datetime_format)


class ResCompany(models.Model):
    _inherit = 'res.company'

    report_logo = fields.Binary(string="SR Report Logo")
    sr_report_header = fields.Html(string='SR Company Tagline', help="Appears for SR Boxed Bordered, on the top right corner of your printed documents (report header).")

    @property
    def _current_date(self):
        lang = get_lang(self.env, self.env.user.lang)
        date_format = lang.date_format
        time_format = lang.time_format
        datetime_format = date_format + " " + time_format
        return fields.Datetime.context_timestamp(self, fields.Datetime.now()).strftime(datetime_format)

    @property
    def _current_user(self):
        return self.env.user
