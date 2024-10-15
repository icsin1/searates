from odoo import models

DYNAMIC_FIELDS = ['shipment_partner_ids']


class DocXTemplate(models.Model):
    _inherit = 'docx.template'

    def _generate_dynamic_fields(self, row, model, sheet, field_type, field, add_technical_name=False):
        row = super()._generate_dynamic_fields(row, model, sheet, field_type, field, add_technical_name=add_technical_name)
        if field and field.name in DYNAMIC_FIELDS:
            method = "_generate_{}_fields".format(field.name)
            if hasattr(self, method):
                field_method = getattr(self, method)
                return field_method(row, sheet, field)
        return row

    def _to_party_key(self, party_type):
        field_name = party_type.name.capitalize().replace(" ", '_').replace("(", "_").replace(")", "_")
        field_name = self._key_to_camel_case("party_{}".format(field_name))
        return field_name

    def _generate_shipment_partner_ids_fields(self, row, worksheet, field):
        party_types = self.env['res.partner.type'].sudo().search([])
        for party_type in party_types:
            row += 1
            field_name = self._to_party_key(party_type)
            self._add_dynamic_field_row(worksheet, field_name, party_type.name, row)
        return row

    def _convert_to_dict_dynamic_rows(self, record, field_name, field_type, records):
        values = super()._convert_to_dict_dynamic_rows(record, field_name, field_type, records)
        values = {}
        if field_name in DYNAMIC_FIELDS:
            for rec in records:
                values[self._to_party_key(rec.partner_type_id)] = rec.partner_id.name
        return values
