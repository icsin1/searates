# -*- coding: utf-8 -*-

import re

from odoo import models, _


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    def _is_enabled_by_default_on_journal(self, journal):
        self.ensure_one()
        if self.code == "edi_sr_env":
            return journal.company_id.country_id.code == 'IN'
        return super()._is_enabled_by_default_on_journal(journal)

    def _is_required_for_invoice(self, invoice):
        self.ensure_one()
        if self.code == "edi_sr_env":
            return invoice.is_sale_document() and invoice.country_code == 'IN' and invoice.l10n_in_gst_treatment in (
                "regular",
                "composition",
                "overseas",
                "special_economic_zone",
                "deemed_export",
            )
        return super()._is_required_for_invoice(invoice)

    def _l10n_in_validate_partner(self, partner, is_company=False):
        self.ensure_one()
        message = []
        if not re.match("^.{3,100}$", partner.street or ""):
            message.append(_("\n- Street required min 3 and max 100 characters"))
        if partner.street2 and not re.match("^.{3,100}$", partner.street2):
            message.append(_("\n- Street2 should be min 3 and max 100 characters"))
        if not re.match("^.{3,100}$", partner.city_id.name or partner.city or ""):
            message.append(_("\n- City required min 3 and max 100 characters"))
        if not re.match("^.{3,50}$", partner.state_id.name or ""):
            message.append(_("\n- State required min 3 and max 50 characters"))
        if partner.country_id.code == "IN" and not re.match("^[0-9]{6,}$", partner.zip or ""):
            message.append(_("\n- Zip code required 6 digits"))
        if partner.phone and not re.match("^[0-9]{10,12}$", self._l10n_in_edi_extract_digits(partner.phone)):
            message.append(_("\n- Mobile number should be minimum 10 or maximum 12 digits"))
        if partner.email and (
            not re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", partner.email)
            or not re.match("^.{6,100}$", partner.email)
        ):
            message.append(_("\n- Email address should be valid and not more then 100 characters"))
        return message

    def _check_move_configuration(self, move):
        if self.code != "edi_sr_env":
            return super()._check_move_configuration(move)

        error_message = []
        error_message += self._l10n_in_validate_partner(move.partner_id)
        error_message += self._l10n_in_validate_partner(move.company_id.partner_id, is_company=True)
        if not re.match("^.{1,16}$", move.name):
            error_message.append(_("Invoice number should not be more than 16 characters"))
        for line in move.invoice_line_ids.filtered(lambda line: not (line.display_type or line.is_rounding_line)):
            if line.product_id:
                hsn_code = self._l10n_in_edi_extract_digits(line._get_l10n_in_hsn_code())
                if not hsn_code:
                    error_message.append(_("HSN code is not set in product %s", line.product_id.name))
                elif not re.match("^[0-9]+$", hsn_code):
                    error_message.append(_(
                        "Invalid HSN Code (%s) in product %s", hsn_code, line.product_id.name
                    ))
            else:
                error_message.append(_("product is required to get HSN code"))
        return error_message

    def _l10n_in_edi_extract_digits(self, string):
        if not string:
            return string
        matches = re.findall(r"\d+", string)
        result = "".join(matches)
        return result
