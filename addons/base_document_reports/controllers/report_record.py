import base64
import logging

from odoo import http, fields, _
from odoo.http import request
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError
from .web_actions import WebAction


_logger = logging.getLogger(__name__)

IGNORE_MODEL_FIELDS = ['__last_update', 'write_uid', 'create_uid', 'product_tmpl_id', 'product_variant_id', 'message_partner_ids', 'message_ids', 'move_ids', 'totp_secret']
IGNORE_FIELD_KEYS = ['my_activity_', 'activity_', 'message_', 'website_message_']


class ReportRecordWebController(WebAction):

    @http.route('/web/action/report/read_record', auth='user', type='json')
    def report_record_read(self, action_id, model_id, res_ids, **kwargs):
        Actions = request.env['ir.actions.actions'].sudo()
        action_id = self._get_action_id(action_id)
        base_action = Actions.browse([action_id]).read(['type'])
        if not base_action:
            raise UserError(_('Unable to find Report Action'))
        ctx = dict(request.context)
        action_type = base_action[0]['type']
        request.context = ctx
        # ir.actions.report
        report = request.env[action_type].sudo().browse([action_id])

        # document report engine template
        report_template = request.env[report.report_res_model].sudo().browse(report.report_res_id)
        ctx.update(report_template._get_context())
        Model = request.env[report_template.report_id.binding_model_id.model].sudo()
        record = Model.browse(res_ids[0])
        template_obj = report_template._get_template(record)
        template_file = base64.b64decode(template_obj[report_template._template_field])

        # _record_to_json and _find_template attributes are under sub modules
        if hasattr(report_template.report_id, '_record_to_json') and hasattr(report_template, '_find_template'):
            report_template_obj = report_template._find_template(record)
            record_dict = report_template.report_id.with_context(ctx)._record_to_json(record, json_spec=report_template_obj.json_spec_id)
        else:
            record_dict = self.with_context(ctx)._parse_record_to_dict(record)
        return {
            'template': template_file,
            'record': record_dict,
            'context': {
                'action_id': action_id,
                'res_id': res_ids[0],
                'res_model': record._name,
                'report_template': report_template.id,
                **report_template._get_context()
            }
        }

    def _parse_record_to_dict(self, record):
        record.ensure_one()
        model_fields = record._fields
        record_dict = {}
        for field_name in model_fields:
            if not any([field_name.startswith(ignore_key) for ignore_key in IGNORE_FIELD_KEYS]) and field_name not in IGNORE_MODEL_FIELDS:
                field = model_fields[field_name]
                method_name = f'_parse_field_{field.type}'
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    record_dict[field_name] = method(field, record)
                else:
                    record_dict[field_name] = record[field_name]
        return record_dict

    def _first_level_record_to_dict(self, rel_record):
        rel_record.ensure_one()
        model_fields = rel_record._fields
        record_dict = {}
        for field_name in model_fields:
            if not any([field_name.startswith(ignore_key) for ignore_key in IGNORE_FIELD_KEYS]) and field_name not in IGNORE_MODEL_FIELDS:
                record_value = rel_record[field_name]
                field = model_fields[field_name]
                method_name = f'_parse_field_{field.type}'
                if field.type in ['many2one']:
                    record_dict[field_name] = record_value and [record_value.id, record_value.display_name] or False
                elif field.type in ['many2many', 'one2many']:
                    record_dict[field_name] = [[x2m_rec.id, x2m_rec.display_name] for x2m_rec in record_value]
                elif hasattr(self, method_name):
                    method = getattr(self, method_name)
                    record_dict[field_name] = method(field, rel_record)
                else:
                    record_dict[field_name] = rel_record[field_name]
        return record_dict

    # Field parsers

    def _parse_field_datetime(self, field, record):
        datetime_obj = record[field.name]
        if datetime_obj:
            return fields.Datetime.to_string(datetime_obj)
        return False

    def _parse_field_date(self, field, record):
        date_obj = record[field.name]
        if date_obj:
            return fields.Date.to_string(date_obj)
        return False

    def _parse_field_binary(self, field, record):
        record_value = record[field.name]
        if record_value:
            try:
                return record_value.decode('utf-8')
            except Exception as e:
                _logger.warning("Field Parse issue for Field {} of type {} on model {} : {}".format(
                    field.name, field.type, record._name, str(e)
                ))
        return False

    def _parse_field_many2one(self, field, record):
        record_value = record[field.name]
        if record_value:
            return self._first_level_record_to_dict(record[field.name])
        return False

    def _parse_field_monetary(self, field, record):
        record_value = record[field.name]
        currency_field = field.currency_field or 'currency_id'
        if currency_field in record:
            return formatLang(request.env, record_value, currency_obj=record[currency_field] or request.env.company.currency_id)
        return record_value

    def _parse_field_selection(self, field, record):
        record_value = record[field.name]
        return [record_value, dict(field._description_selection(request.env)).get(record_value)]

    def _parse_field_one2many(self, field, record):
        records = record[field.name]
        return [self._first_level_record_to_dict(o2m_record) for o2m_record in records]

    def _parse_field_many2many(self, field, record):
        records = record[field.name]
        return [self._first_level_record_to_dict(m2m_record) for m2m_record in records]

    def _parse_field_html(self, field, record):
        return record[field.name]
