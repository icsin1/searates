# -*- coding: utf-8 -*-
from odoo import models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _l10n_in_get_indian_state(self, partner):
        res = super()._l10n_in_get_indian_state(partner)
        if partner.l10n_in_gst_treatment in ['overseas']:
            return self.env.ref('l10n_in.state_in_oc')
        return res

    def _get_is_tax_reverse_charge(self):
        self.ensure_one()
        if self.company_id.country_id.code == 'IN':
            return bool(self.invoice_line_ids.mapped('tax_ids').filtered(lambda tax: tax.l10n_in_reverse_charge))
        return super()._get_is_tax_reverse_charge()

    def _get_is_overseas(self):
        self.ensure_one()
        if self.company_id.country_id.code == 'IN':
            return self.l10n_in_gst_treatment == 'overseas' or self.partner_id.country_id.code != self.company_id.country_id.code or False
        return super()._get_is_overseas()

    def _get_supply_type(self):
        self.ensure_one()
        if self.company_id.country_id.code == 'IN':
            supply_type_mapping = {
                "regular": "B2B",
                "special_economic_zone": "SEZWOP" if self.l10n_in_export_type and self.l10n_in_export_type == "without_payment" else 'SEZWP',
                "overseas": "EXPWOP" if self.l10n_in_export_type and self.l10n_in_export_type == "without_payment" else 'EXPWP',
                "deemed_export": "DEXP"
            }
            return supply_type_mapping.get(self.l10n_in_gst_treatment, 'B2B')
        return super()._get_supply_type()

    def _get_export_details(self):
        self.ensure_one()
        if self.company_id.country_id.code == 'IN':
            return {
                'shipping_bill_number': self.l10n_in_shipping_bill_number or None,
                'shipping_bill_date': self.l10n_in_shipping_bill_date and str(self.l10n_in_shipping_bill_date) or None,
                'shipping_port_code': self.l10n_in_shipping_port_code_id.code or None
            }
        return super()._get_export_details()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_l10n_in_hsn_code(self):
        self.ensure_one()
        return self.product_id.l10n_in_hsn_code

    def _get_edi_product_identifier(self):
        self.ensure_one()
        if self.move_id.country_code == 'IN':
            return self.product_id and self.product_id.l10n_in_hsn_code or str(self.id)
        return super()._get_edi_product_identifier()

    def _get_product_unit(self):
        self.ensure_one()
        if self.move_id.country_code == 'IN':
            return self.product_uom_id.l10n_in_code and self.product_uom_id.l10n_in_code.split("-")[0] or "OTH"
        return super()._get_product_unit()

    def _get_edi_tax_code(self, tax, tax_line):
        self.ensure_one()
        if self.move_id.country_code == 'IN':
            line_code = "other"

            tax_tag_ids = tax.invoice_repartition_line_ids.tag_ids | tax.refund_repartition_line_ids.tag_ids

            tax_report_line_sc = self.env.ref("l10n_in.tax_report_line_state_cess", False)
            tax_report_line_cess = self.env.ref("l10n_in.tax_report_line_cess", False)
            if any(tag in tax_tag_ids for tag in tax_report_line_cess.sudo().tag_ids):
                if tax.amount_type != "percent":
                    line_code = "cess_non_advol"
                else:
                    line_code = "cess"
            elif tax_report_line_sc and any(tag in tax_tag_ids for tag in tax_report_line_sc.sudo().tag_ids):
                if tax.amount_type != "percent":
                    line_code = "state_cess_non_advol"
                else:
                    line_code = "state_cess"
            else:
                for gst in ["cgst", "sgst", "igst"]:
                    tag_ids = self.env.ref("l10n_in.tax_report_line_%s" % (gst)).sudo().tag_ids
                    if any(tag in tax_tag_ids for tag in tag_ids):
                        line_code = gst
            return line_code
        return super()._get_edi_tax_code(tax, tax_line)
