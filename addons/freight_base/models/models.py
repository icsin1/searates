# -*- coding: utf-8 -*-

from odoo import models, api


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('_ignore_freight_sequence', False):
            freight_sequence_id = self.env['freight.sequence'].sudo().search([('company_id', '=', self.env.company.id), ('ir_model_id.model', '=', self._name)])
            if not freight_sequence_id:
                return records

            for rec in records:
                to_update_values = {}
                for ir_field in freight_sequence_id.mapped('ir_field_id'):
                    freight_sequences = freight_sequence_id.filtered(lambda fs: fs.ir_field_id == ir_field)
                    matched_sequence = freight_sequences._match_record(rec)
                    for freight_seq in matched_sequence:
                        to_update_values.update({freight_seq.ir_field_id.name: freight_seq.get_dynamic_model_sequence(rec)})
                rec.write(to_update_values)
        return records
