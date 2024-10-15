from odoo import models, fields, api

class CustomAccountTax(models.Model):
    _inherit = 'account.tax'

    @api.onchange('tax_group_id')
    def onchange_tax_group_id(self):
        gst_tax_group = [self.env.ref('l10n_in.sgst_group').id,
                        self.env.ref('l10n_in.cgst_group').id,
                        self.env.ref('l10n_in.igst_group').id,
                        self.env.ref('l10n_in.gst_group').id,
                        self.env.ref('l10n_in.non_gst_supplies_group').id,
                        self.env.ref('l10n_in.exempt_group').id,
                        self.env.ref('l10n_in.nil_rated_group').id,
        ]
        tds_tax_group = [self.env.ref('l10n_in_tds_tcs.tds_group').id]
        tcs_tax_group = [self.env.ref('l10n_in_tds_tcs.tcs_group').id]
        cess_tax_group = [self.env.ref('l10n_in.cess_group').id]
        if self.country_id and self.country_id.code == 'IN':
            if self.tax_group_id.id in gst_tax_group or self.tax_group_id.id in cess_tax_group:
                self.price_include = False
                self.include_base_amount = True
                self.is_base_affected = False
                self.l10n_in_reverse_charge = False
            elif self.tax_group_id.id in tcs_tax_group:
                self.price_include = False
                self.include_base_amount = False
                self.is_base_affected = True
                self.l10n_in_reverse_charge = False
            elif self.tax_group_id.id in tds_tax_group:
                self.price_include = False
                self.include_base_amount = False
                self.is_base_affected = False
                self.l10n_in_reverse_charge = False
