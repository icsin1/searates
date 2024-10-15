from odoo import models


FIELDS = ['terms_ids']
MODELS = ['freight.house.shipment', 'freight.master.shipment']
TERMS_CONDITION_KEY = 'TermsAndConditions'


class DocXShipmentTermsAndConditionsTemplate(models.Model):
    _inherit = 'docx.template'

    def _get_terms_and_condition_for_document(self, record):
        if record and 'terms_ids' in record:
            if not record.terms_ids:
                return self._html_to_text(self.terms_and_conditions)
            terms = record.terms_ids.filtered(lambda t: t.document_type_id in self.document_type_ids)
            if terms:
                return self._html_to_text(terms[0].terms_and_conditions)
        return ''

    def _generate_dynamic_fields(self, row, model, sheet, field_type, field, add_technical_name=False):
        row = super()._generate_dynamic_fields(row, model, sheet, field_type, field, add_technical_name=add_technical_name)
        if self.res_model_id.model in MODELS and field.name in FIELDS:
            field_desc = "{} Terms and Conditions".format(self.res_model_id.name)
            self._add_dynamic_field_row(sheet, TERMS_CONDITION_KEY, field_desc, row)
        return row

    def _convert_to_dict_dynamic_rows(self, record, field_name, field_type, records):
        values = super()._convert_to_dict_dynamic_rows(record, field_name, field_type, records)
        if self.res_model_id.model in MODELS:
            values[TERMS_CONDITION_KEY] = self._get_terms_and_condition_for_document(record)
        return values
