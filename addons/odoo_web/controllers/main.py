# -*- coding: utf-8 -*-

import json

import odoo
from odoo import http
from odoo.tools.func import lazy
from odoo.tools import pycompat, osutil
from odoo.tools.misc import get_lang
from odoo.http import request, content_disposition
from odoo.addons.web.controllers.main import ExportXlsxWriter, ExcelExport,GroupsTreeNode
from odoo.addons.odoo_base import tools
from odoo.osv.query import Query

## for solvong excel issue
import operator

ExcelDateFormatAbbreviations = {
    'a': 'ddd',
    'A': 'dddd',
    'b': 'mmm',
    'B': 'mmmm',
    'd': 'dd',
    'H': 'hh',
    'I': 'HH',
    'M': 'mm',
    'p': 'AM/PM',
    'S': 'ss',
    'y': 'yy',
    'Y': 'yyyy',
    'm': 'mm',
    'j': '',
    'w': '',
}


def _convert_date_time_format_to_xls_format(format_string):
    """
    Convert python strftime format to excel date & time format
    :param format_string:
    :return:
    """
    converted_format = []
    percent_char = False
    for char in format_string:
        if percent_char and char in ExcelDateFormatAbbreviations:
            converted_format.append(ExcelDateFormatAbbreviations[char])
        elif char == "%":
            percent_char = True
        else:
            converted_format.append(char)
    return "".join(converted_format)


class Controller(http.Controller):

    @http.route('/dashboard/group_by', auth='user', type='json')
    def dashboard_data(self, model=False, domain=False, group_by=False, labelField='Label', dataField='Value', limit=None, offset=0, sort=True, dataFields=False, count=False, **kwargs):
        record = request.env[model].with_context(**kwargs.get('context', {}))
        group_by = isinstance(group_by, str) and [group_by] or group_by
        if count:
            allowed_company_ids = record._context.get('allowed_company_ids', [])
            if allowed_company_ids and hasattr(record, 'company_id'):
                domain += [('company_id', 'in', allowed_company_ids)]
            query = record._where_calc(domain)
            table, where_clause, where_params = query.get_sql()

            request.env.cr.execute(f"""
                SELECT COUNT(id)
                From {table}
                WHERE {where_clause}
                GROUP BY {group_by[0]}
            """, where_params)
            return len(request.env.cr.fetchall())

        field_data = record.fields_get(group_by)[group_by[0]]

        def getFieldValue(line, field):
            if field_data['type'] == 'selection':
                return dict(field_data['selection'])[line[group_by[0]]]
            elif field_data['type'] == 'many2one':
                return line[field] and line[field][1]
            else:
                return line.get(field)

        tableData = []
        fields = list(dataFields.keys()) if dataFields else group_by
        for line in record.read_group(domain, fields, group_by, offset=offset, lazy=count):
            values = {}
            values[labelField] = getFieldValue(line, group_by[0]) or 'Not Available'
            if dataFields:
                for field, label in dataFields.items():
                    field = field.split(':')
                    # operator = 'len'
                    if len(field) == 2:
                        field, operator = field
                        values[label] = line.get(field)
                    elif field and field[0] not in line:
                        field = field[0]
                        values[label] = line.get('__count', 0)
                    else:
                        values[label] = line.get(field[0])
            else:
                values[dataField] = line.get('__count')
            values['__domain'] = line.get('__domain', [])
            tableData.append(values)

        if isinstance(sort, bool):
            tableData.sort(key=lambda x: x[dataField], reverse=True)
        elif isinstance(sort, list):
            tableData = sorted(tableData, key=lambda x: sort.index(x[labelField]) if x[labelField] in sort else float('inf'))

        return tableData[offset: limit]

    @http.route('/app/version_info', type='json', auth="none")
    def get_version_info(self):
        # Clubbing application and server version in app/version API
        version_data = tools.get_version_info()
        rpc_version_1 = {
            'application_version': version_data.get('version'),
            'application_version_info': version_data.get('version_info', []),
            'application_serie': version_data.get('serie'),
            'website': version_data.get('url'),
            'release_date': version_data.get('release_date'),
            'protocol_version': 1,
            **odoo.service.common.exp_version()
        }
        return rpc_version_1

    @http.route('/user_has_groups', auth='user', type='json')
    def user_has_groups(self, groups):
        return request.env.user.user_has_groups(groups)


class SpreadSheetExport(ExcelExport):
    # for fixing the sorting issue override the base function and changed two lines of code at 163 to 166
    def base(self, data):
        params = json.loads(data)
        model, fields, ids, domain, import_compat = \
            operator.itemgetter('model', 'fields', 'ids', 'domain', 'import_compat')(params)

        Model = request.env[model].with_context(import_compat=import_compat, **params.get('context', {}))
        if not Model._is_an_ordinary_table():
            fields = [field for field in fields if field['name'] != 'id']

        field_names = [f['name'] for f in fields]
        if import_compat:
            columns_headers = field_names
        else:
            columns_headers = [val['label'].strip() for val in fields]

        groupby = params.get('groupby')
        if not import_compat and groupby:
            groupby_type = [Model._fields[x.split(':')[0]].type for x in groupby]
            domain = [('id', 'in', ids)] if ids else domain
            groups_data = Model.read_group(domain, [x if x != '.id' else 'id' for x in field_names], groupby, lazy=False)

            # read_group(lazy=False) returns a dict only for final groups (with actual data),
            # not for intermediary groups. The full group tree must be re-constructed.
            tree = GroupsTreeNode(Model, field_names, groupby, groupby_type)
            for leaf in groups_data:
                tree.insert_leaf(leaf)

            response_data = self.from_group_data(fields, tree)
        else:
            if len(domain) == 1 and 'id' in domain[0]:
                records = Model.browse(domain[0][2])
            else:
                records = Model.browse(ids) if ids else Model.search(domain, offset=0, limit=False, order=False)
            export_data = records.export_data(field_names).get('datas',[])
            response_data = self.from_data(columns_headers, export_data)

        # TODO: call `clean_filename` directly in `content_disposition`?
        return request.make_response(response_data,
            headers=[('Content-Disposition',
                            content_disposition(
                                osutil.clean_filename(self.filename(model) + self.extension))),
                     ('Content-Type', self.content_type)],
        )

    @http.route('/odoo_web/export/xlsx', type='http', auth="user")
    def spread_sheet_index(self, data):
        return self.generate_xlsx(data)

    def spread_sheet_from_data(self, fields, rows):
        ignore_fields = [index for index, value in enumerate(fields) if value.startswith('__')]
        with ExportXlsxWriter(list(filter(lambda element: not element.startswith('__'), fields)), len(rows)) as xlsx_writer:
            for row_index, row in enumerate(rows):
                for cell_index, cell_value in enumerate(row):
                    if cell_index in ignore_fields:
                        continue
                    if isinstance(cell_value, (list, tuple)):
                        cell_value = pycompat.to_text(cell_value)
                    if type(cell_value) == lazy:
                        cell_value = cell_value._value
                    xlsx_writer.write_cell(row_index + 1, cell_index, cell_value)

        return xlsx_writer.value

    def generate_xlsx(self, data):
        params = json.loads(data)

        if {'filename', 'model'} - params.keys():
            if 'fields' not in params.keys() and 'field_names' in params.keys():
                params['fields'] = self.get_fields(model=params.get('model'), fields=params.get('field_names'))
            return self.index(json.dumps(params))

        filename = params['filename']
        if params.get('method'):
            res = getattr(request.env[params['model']].with_context(**params.get('context', {})), params['method'])(*params['args'], **params['kwargs'])
        else:

            res = Controller.dashboard_data(request.env[params['model']], **params['kwargs'])

        fields = res and list(res[0])
        rows = res and list(map(lambda x: list(x.values()), res))

        response_data = rows and self.spread_sheet_from_data(fields=fields, rows=rows)
        return request.make_response(
            response_data,
            headers=[(
                'Content-Disposition',
                content_disposition(osutil.clean_filename(filename + self.extension))),
                ('Content-Type', self.content_type)
            ])

    def fields_get(self, model, fields=[]):
        Model = request.env[model]
        fields = Model.fields_get(fields)
        return fields

    def get_fields(self, model, fields=[]):
        records = []
        field_list = self.fields_get(model, fields=fields)

        for field_name, field in sorted(field_list.items(), key=lambda x: fields.index(x[0])):
            if not field.get('exportable', True):
                continue

            records.append({
                'id': field_name,
                'string': field['string'],
                'name': field_name,
                'label': field['string'],
                'value': field_name,
                'children': False,
                'field_type': field.get('type'),
                'required': field.get('required'),
                'relation_field': field.get('relation_field')
            })
        return records


class CustomExcelExport(ExcelExport):

    def from_data(self, fields, rows):
        """
            Override to change the default date and time
            formats to the current language time and date formats.
        """
        with ExportXlsxWriter(fields, len(rows)) as xlsx_writer:
            lang = get_lang(request.env)
            date_format = _convert_date_time_format_to_xls_format(lang.date_format)
            xlsx_writer.date_style = xlsx_writer.workbook.add_format({
                'text_wrap': True,
                'num_format': date_format
            })
            time_format = _convert_date_time_format_to_xls_format(lang.time_format)
            lang_datetime_format = "{} {}".format(date_format, time_format)
            xlsx_writer.datetime_style = xlsx_writer.workbook.add_format({
                'text_wrap': True,
                'num_format': lang_datetime_format
            })
            for row_index, row in enumerate(rows):
                for cell_index, cell_value in enumerate(row):
                    if isinstance(cell_value, (list, tuple)):
                        cell_value = pycompat.to_text(cell_value)
                    xlsx_writer.write_cell(row_index + 1, cell_index, cell_value)
        return xlsx_writer.value
