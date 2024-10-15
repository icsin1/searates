from odoo import models, fields, api


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    print_timestamp_user_at_footer = fields.Boolean(string='Print Timestamp/User at Footer', related='company_id.allow_report_print_datetime_log', readonly=False)

    @api.depends('print_timestamp_user_at_footer', 'report_layout_id', 'logo', 'font', 'primary_color', 'secondary_color', 'report_header', 'report_footer', 'layout_background', 'layout_background_image', 'company_details')
    def _compute_preview(self):
        return super()._compute_preview()

    def _get_report_footer_print_log(self):
        self.ensure_one()
        return self.company_id._get_report_footer_print_log()

    def allow_print_timestamp(self):
        return self.print_timestamp_user_at_footer
