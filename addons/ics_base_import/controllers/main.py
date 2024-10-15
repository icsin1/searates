# -*- coding: utf-8 -*-

import base64
import io
from odoo import http
from odoo.http import request, content_disposition
from odoo.tools.misc import xlsxwriter


class ICSImportController(http.Controller):

    def _get_model_to_name(self, model_obj):
        return "{} ({})".format(model_obj.name, model_obj.model)

    def _get_model_obj(self, model_name):
        return request.env['ir.model'].sudo().search([('model', '=', model_name)])

    @http.route('/base/export/importer_file/<string:model_name>', methods=['GET'], auth='user')
    def set_file(self, model_name):
        model_obj = self._get_model_obj(model_name)

        xls_content = self._generate_importer_file(model_obj)
        content_base64 = base64.b64decode(xls_content)
        file_name = 'Data-Importer-{}.xlsx'.format(model_name.replace(".", '-'))
        return request.make_response(content_base64, [
            ('Content-Type', 'application/octet-stream'),
            ('Content-Length', len(xls_content)),
            ('Content-Disposition', content_disposition(file_name))
        ])

    def _get_filtered_fields(self, model):
        IGNORE_MODELS = ['mail.message', 'mail.activity']
        IGNORE_FIELDS = ['id', 'write_uid', 'create_uid', 'create_date', 'write_date', 'display_name', 'active']
        IGNORE_TTYPE = ['binary']
        fields = model.field_id.filtered(
            lambda f: f.ttype not in IGNORE_TTYPE and f.relation not in IGNORE_MODELS and f.name not in IGNORE_FIELDS and
            f.store and not (f.readonly and not f.required) and
            not f.name.startswith('__') and not f.name.startswith('activity_') and not f.name.startswith('message_')
        )
        return fields.sorted('required', reverse=True)

    def _generate_importer_file(self, model):
        sheets = []
        fields = self._get_filtered_fields(model)

        # Main model
        sheets.append({'name': self._get_model_to_name(model), 'fields': fields.filtered(lambda f: f.ttype not in ['many2many', 'one2many'])})

        # x2m models
        x2m_fields = fields.filtered(lambda f: f.ttype in ['many2many', 'one2many'])
        for x2m_field in x2m_fields:
            x2m_model = self._get_model_obj(x2m_field.relation)
            x2m_fields = self._get_filtered_fields(x2m_model)
            sheets.append({'name': '{} ({})'.format(x2m_field.name, x2m_field.relation), 'fields': x2m_fields.filtered(lambda f: f.ttype not in ['many2many', 'one2many']), 'parent': model})
        return self._fields_to_file(model, sheets)

    def _fields_to_file(self, model, sheets):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        required_style = workbook.add_format({'bold': True, 'font_size': '12px'})
        normal_style = workbook.add_format({'font_size': '12px'})

        for sheet in sheets:
            # Creating sheet
            worksheet = workbook.add_worksheet(sheet.get('name'))
            worksheet.write(0, 0, 'ID', required_style)  # HARD CODE AT FIRST
            worksheet.write_comment(0, 0, "Technical Name: id\nRequired Field: Yes\nHelp: External identifier use unique id as string")
            col = 1
            for field in sheet.get('fields', []):
                required_field = field.required
                if field.name == 'name':
                    required_field = True
                worksheet.set_column(0, col, len(field.field_description))
                worksheet.write(0, col, field.field_description, required_field and required_style or normal_style)
                relation_help = '\nRequired Field: {}'.format('Yes' if required_field else 'No')
                if field.relation:
                    relation_help += '\nData Model Relation: {}'.format(field.relation)
                other_help_text = 'Data Type: {}\n'.format(field.ttype)
                if field.ttype == 'selection':
                    other_help_text += '\nPossible Values: {}\n\n'.format(', '.join(field.selection_ids.mapped('value')))
                    for selection in field.selection_ids:
                        other_help_text += '{} : {}\n'.format(selection.value, selection.name)
                worksheet.write_comment(0, col, "Technical Name: {}{}\nHelp: {}\n{}".format(
                    field.name, relation_help, field.help or field.field_description, other_help_text
                ))
                col += 1

        # Generating content
        workbook.close()
        return base64.b64encode(output.getvalue())
