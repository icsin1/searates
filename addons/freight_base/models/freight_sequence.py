# -*- coding: utf-8 -*-

import ast
from odoo import models, fields, api


class FreightSequence(models.Model):
    _name = "freight.sequence"
    _description = 'Freight Sequence'
    _order = 'sequence,ir_model_id,name'

    name = fields.Char(required=True)
    ir_model_id = fields.Many2one('ir.model', string='Model', required=True, copy=False, ondelete='cascade')
    date_field_id = fields.Many2one('ir.model.fields', domain="[('model_id', '=', ir_model_id), ('ttype', 'in', ['date', 'datetime'])]", string='Date Field')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, readonly=True)
    ir_sequence_id = fields.Many2one('ir.sequence', string='Sequence', required=True, copy=False)
    sequence_format = fields.Char('Format', required=True)
    number_increment = fields.Integer(related='ir_sequence_id.number_increment', store=True, readonly=False, required=True)
    padding = fields.Integer(related='ir_sequence_id.padding', store=True, readonly=False, required=True)
    preview = fields.Char(compute='_preview_sequence_format')
    ir_field_id = fields.Many2one('ir.model.fields', string='Field', required=True, copy=False, ondelete='cascade',
                                  domain="[('model_id', '=', ir_model_id),('ttype', '=', 'char'), ('store', '=', True)]")
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=0, string='Sequence #')

    # Freight product based sequence
    freight_product_id = fields.Many2one('freight.product', string='Freight Product')

    _sql_constraints = [
        ('unique_company_per_model', 'unique(ir_model_id, company_id, ir_field_id, freight_product_id)', 'The Serial Number must be unique per model, field & company!')
    ]

    @api.depends('sequence_format', 'ir_model_id')
    def _preview_sequence_format(self):
        for rec in self:
            preview_seq = ''
            if rec.ir_model_id and rec.sequence_format:
                record_id = self.env[rec.ir_model_id.model].search([], limit=1)
                preview_seq = rec.action_get_record_sequence(record_id)
            rec.preview = preview_seq

    def action_get_record_sequence(self, record_id):
        sequence = ''
        if record_id:
            sequence = self.env['mail.render.mixin']._render_template(self.sequence_format, self.ir_model_id.model, [record_id.id])[record_id.id]
        return sequence

    def _get_model_next_sequence_number(self, record):
        ir_seq = self.ir_sequence_id
        if self.date_field_id:
            ir_seq = ir_seq.with_context(ir_sequence_date=record[self.date_field_id.name])
        return ir_seq.next_by_id()

    def get_dynamic_model_sequence(self, record_id):
        return '{}{}'.format(self.action_get_record_sequence(record_id),
                             self._get_model_next_sequence_number(record_id))

    @api.onchange('ir_model_id')
    def _onchange_ir_model_id(self):
        fields_list = ['ir_field_id', 'sequence_format', 'ir_sequence_id']
        self.update({field: False for field in fields_list})

    def _match_record(self, record):
        # Single sequence
        if len(self) < 2:
            return self

        # No any freight product based sequence
        freight_product_seq = self.filtered(lambda fs: fs.freight_product_id)
        if not freight_product_seq:
            return self

        # Matching sequence
        for fs in freight_product_seq:
            product_domain = ast.literal_eval(fs.freight_product_id.match_domain)
            matched = self.env[fs.ir_model_id.model].sudo().search(product_domain + [('id', '=', record.id)])
            if matched:
                return fs

        # Default sequence as self
        non_freight_seq = self - freight_product_seq
        return non_freight_seq[0] if non_freight_seq else []
