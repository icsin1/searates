# -*- coding: utf-8 -*-
import markupsafe

from odoo import api, models
from odoo.tools import is_html_empty


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    @api.depends('report_layout_id', 'logo', 'font', 'primary_color', 'secondary_color', 'report_header', 'report_footer', 'layout_background', 'layout_background_image', 'company_details')
    def _compute_preview(self):
        """ compute a qweb based preview to display on the wizard
            Override to pass is_html_empty in template rendering to prevent traceback of null value in HTML check after layout template inherited"""
        styles = self._get_asset_style()

        for wizard in self:
            if wizard.report_layout_id:
                # guarantees that bin_size is always set to False,
                # so the logo always contains the bin data instead of the binary size
                if wizard.env.context.get('bin_size'):
                    wizard_with_logo = wizard.with_context(bin_size=False)
                else:
                    wizard_with_logo = wizard
                preview_css = markupsafe.Markup(self._get_css_for_preview(styles, wizard_with_logo.id))
                ir_ui_view = wizard_with_logo.env['ir.ui.view']
                wizard.preview = ir_ui_view._render_template('web.report_invoice_wizard_preview', {'company': wizard_with_logo, 'preview_css': preview_css, 'is_html_empty': is_html_empty})
            else:
                wizard.preview = False

    @api.onchange('company_details')
    def set_company_details(self):
        if not self.company_details:
            return True
        self.company_details = '<br>'.join(self.company_details.split('<br>')[:3])
