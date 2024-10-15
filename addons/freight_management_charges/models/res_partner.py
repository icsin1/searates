# -*- coding: utf-8 -*-

from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def update_vendor_tag(self):
        vendor_party = self.env.ref('freight_base.org_type_vendor', raise_if_not_found=False)
        if vendor_party:
            self.write({'category_ids': [(4, vendor_party.id)]})
