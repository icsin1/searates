from odoo import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_edi_customer_identifiers(self):
        ret = [{
            'identifier_key': '{}:{}'.format(rec.country_id.code, rec.country_id.vat_label) if rec.l10n_in_gst_treatment in ['overseas', 'deemed_export', 'special_economic_zone'] else 'vat',
            'identifier_label': rec.country_id.vat_label,
            'identifier_value': rec.vat or 'URP',
        } for rec in self]
        return ret

    @api.onchange('l10n_in_gst_treatment')
    def _onchange_gst_treatment(self):
        if self.l10n_in_gst_treatment == 'overseas':
            self.update({
                'zip': 999999,
            })
