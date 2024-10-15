from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_edi_customer_identifiers(self):
        return [{
            'identifier_key': 'vat',
            'identifier_label': rec.country_id.vat_label,
            'identifier_value': rec.vat
        } for rec in self]
