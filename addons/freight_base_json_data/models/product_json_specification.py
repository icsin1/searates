import ast
import logging
import base64
import json
import traceback
from pytz import timezone
from datetime import datetime

import odoo
from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import formatLang, format_datetime, format_date, get_lang
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo.tools.float_utils import float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

_logger = logging.getLogger(__name__)


try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None


FIELD_TYPES = [(key, key) for key in sorted(fields.Field.by_type)] + [('computed', 'Computed')]


class ProductJSONSpecification(models.Model):
    _name = 'product.json.specification'
    _description = 'Product Json Specification'

    name = fields.Char(required=True, string='Specification Name')
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', store=True, string='Model Name')
    freight_product_id = fields.Many2one('freight.product')  # DEPRECATED
    product_domain = fields.Text(string='Product Domain', default='[]')
    property_ids = fields.One2many('product.json.specification.property', 'specification_id', string='Properties', copy=True)
    empty_string_for_non_bool = fields.Boolean(string='Empty String (Non-Bool)', default=False)
    keep_structure = fields.Boolean(string='Keep Structure', help='Keeps structure (sub json spec) when no value', default=False)
    description = fields.Text(string='Summary')
    linked_property_ids = fields.One2many('product.json.specification.property', 'property_specification_id', string='Linked Properties', copy=True)
    dependency_spec_ids = fields.One2many('product.json.specification.dependency', 'specification_id', string='Dependency Specification', compute='_compute_dependency_spec_ids', store=True)
    json_specification_data = fields.Binary()
    json_type = fields.Selection([('general', 'General')], default='general', required=True)
    null_for_empty = fields.Boolean(default=False, string='None for Empty Value')

    _sql_constraints = [
        ('product_json_spec_unique', 'unique(name,model_id,json_type)', 'Json Specification must be unique. Same Json Spec with Name and Model Found !')
    ]

    def _get_dependency_properties(self, parent=None):
        self.ensure_one()
        dependency_spec = {}
        for prop in self.property_ids.filtered(lambda prop: prop.property_specification_id):
            key = "{}{}".format(parent or '', prop.name)
            dependency_spec.update({key: (prop, prop.property_specification_id)})
            dependency_spec.update({**prop.property_specification_id._get_dependency_properties(prop.name + " / ")})
        return dependency_spec

    @api.depends('property_ids', 'property_ids.property_specification_id')
    def _compute_dependency_spec_ids(self):
        for rec in self:
            dependency_spec = rec._get_dependency_properties()
            rec.dependency_spec_ids = [(6, False, [])] + [(0, 0, {
                'name': key,
                'property_id': values[0].id,
                'property_specification_id': values[1].id,
            }) for key, values in dependency_spec.items()]

    def copy(self, default=None):
        self.ensure_one()
        chosen_name = default.get('name') if default else ''
        new_name = chosen_name or _('%s (copy)', self.name)
        default = dict(default or {}, name=new_name)
        return super(ProductJSONSpecification, self).copy(default)

    def _get_specs(self):
        self.ensure_one()
        return {prop.name: prop._get_spec() for prop in self.property_ids}

    def action_download_json_spec(self):
        self.ensure_one()
        self.json_specification_data = base64.b64encode(json.dumps(self._get_specs()).encode('utf-8'))
        return {
            'type': 'ir.actions.act_url',
            'name': 'Json Specification',
            'target': 'self',
            'url': '/web/content/%s/%s/json_specification_data/%s.json?download=true' % (self._name, self.id, self.name),
        }

    def _to_empty_structure(self):
        return {prop.name: prop._process_prop_value(False) for prop in self.property_ids}

    def _to_dict(self, record):
        self.ensure_one()
        record_dict = {}
        ctx = self.env.context
        for prop in self.property_ids:
            property_value = prop.with_context(ctx)._get_prop_value(record)
            if prop.is_required and not property_value:
                raise UserError(_('As per JSON Specification {} value must be set to generate JSON'.format(prop.name)))
            record_dict[prop.name] = property_value
        return record_dict

    def get_product_domain(self):
        return ast.literal_eval(self.product_domain or [])

    def _get_importable_json(self):
        self.ensure_one()
        json_spec = {
            'specification_key': self.id,
            'name': self.name,
            'model': self.model_id.model,
            'product_domain': self.product_domain,
            'empty_string_for_non_bool': self.empty_string_for_non_bool,
            'keep_structure': self.keep_structure,
            'description': self.description,
            'json_type': self.json_type,
            'properties': [prop._get_importable_json() for prop in self.property_ids],
            'dependencies': [dep._get_importable_json() for dep in self.property_ids.mapped('property_specification_id')]
        }
        return json_spec

    def action_export_spec_json(self):
        self.ensure_one()
        importable_json = self._get_importable_json()
        self.json_specification_data = base64.b64encode(json.dumps(importable_json).encode('utf-8'))
        return {
            'type': 'ir.actions.act_url',
            'name': 'Importable Json Specification',
            'target': 'self',
            'url': '/web/content/%s/%s/json_specification_data/importable_json_%s.json?download=true' % (self._name, self.id, self.name),
        }


class ProductJSONSpecificationProperty(models.Model):
    _name = 'product.json.specification.property'
    _description = 'Product Json Spec Property'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    name = fields.Char(required=True, string='Property Name')
    specification_id = fields.Many2one('product.json.specification', ondelete='cascade', required=True)
    freight_product_id = fields.Many2one('freight.product', related='specification_id.freight_product_id', store=True)  # DEPRECATED
    product_domain = fields.Text(related='specification_id.product_domain', store=True)
    property_type = fields.Selection([('field', 'Field'), ('prop', 'Property')], default='field', required=True)
    model_id = fields.Many2one('ir.model', related='specification_id.model_id', store=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', store=True, string='Model Name')
    ir_model_field = fields.Many2one('ir.model.fields', domain="[('model_id', '=', model_id)]")
    ir_model_field_name = fields.Char(related='ir_model_field.name', store=True)
    relation_model_id = fields.Many2one('ir.model', string='Relation Model')
    relation_model_name = fields.Char(related='relation_model_id.model', store=True, string='Relation Model Name')
    ttype = fields.Selection(selection=FIELD_TYPES, string='Field Type', required=True)
    is_required = fields.Boolean(default=False)
    property_specification_id = fields.Many2one('product.json.specification', string='Property Specification')
    order_ir_field = fields.Char(string='Order By')
    order_field_type = fields.Selection([('asc', 'ASC'), ('desc', 'DESC')], default='asc')
    description = fields.Text(string='Help')
    noupdate = fields.Boolean(default=False, help='If Checked, at the time of importing json specification it will be ignored')
    raw_value = fields.Boolean(default=False)
    python_code = fields.Text(default="""# Available variables:
#  - env: Environment on which the spec is triggered
#  - model: Property Model of the record on which computation is started; is a void recordset
#  - record: record on which the spec is triggered; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - float_compare: Function to compare floats based on specific precisions
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - UserError: Warning Exception to use with raise
# To return an result, assign: result = {...}
# Note: For relation type of property x2m or m2o you need to return recordset


""")

    _sql_constraints = [
        ('product_json_spec_property_key_unique', 'unique(name,specification_id)', 'Json Specification Property Key must be unique')
    ]

    @api.onchange('ttype')
    def _onchange_ttype(self):
        self.relation_model_id = False
        self.property_specification_id = False

    @api.constrains('python_code')
    def _check_python_code(self):
        for json_property in self.sudo().filtered('python_code'):
            msg = test_python_expr(expr=json_property.python_code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    @api.model
    def _get_eval_context(self, json_property=None):
        """ evaluation context to pass to safe_eval """
        def log(message, level="info"):
            with self.pool.cursor() as cr:
                cr.execute("""
                    INSERT INTO ir_logging(create_date, create_uid, type, dbname, name, level, message, path, line, func)
                    VALUES (NOW() at time zone 'UTC', %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (self.env.uid, 'server', self._cr.dbname, __name__, level, message, "json_property", json_property.id, json_property.name))

        def _num2words(number, lang='en', to='cardinal'):
            if num2words is None:
                return ""
            try:
                return num2words(number, lang=lang, to=to).title()
            except NotImplementedError:
                return num2words(number, lang='en', to=to).title()

        return {
            'uid': self._uid,
            'user': self.env.user,
            'time': tools.safe_eval.time,
            'datetime': tools.safe_eval.datetime,
            'dateutil': tools.safe_eval.dateutil,
            'timezone': timezone,
            'float_compare': float_compare,
            'b64encode': base64.b64encode,
            'b64decode': base64.b64decode,
            # orm
            'env': self.env,
            'model': self.env[json_property.model_id.model],
            # Exceptions
            'Warning': odoo.exceptions.Warning,
            'UserError': odoo.exceptions.UserError,
            # helpers
            'log': log,
            'num2words': _num2words,
            '_property_parser': self
        }

    def _get_importable_json(self):
        self.ensure_one()
        values = self.read(['name', 'property_type', 'model_name', 'ir_model_field_name', 'relation_model_name', 'ttype', 'is_required', 'description', 'python_code'])[0]
        values['property_specification_key'] = self.property_specification_id.id
        return values

    @api.depends('name', 'specification_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '{} ({})'.format(rec.name, rec.specification_id.name)

    @api.onchange('property_type', 'ir_model_field')
    def _onchange_field(self):
        if self.property_type == 'field' and self.ir_model_field:
            self.name = self.ir_model_field.name
            self.description = self.ir_model_field.field_description if not self.description else self.description
            self.ttype = self.ir_model_field.ttype
            self.relation_model_id = self.env['ir.model'].sudo().search([('model', '=', self.ir_model_field.relation)], limit=1)
            self.is_required = self.ir_model_field.required

    def _get_spec(self):
        self.ensure_one()

        spec = {
            'value_type': self.ttype if self.property_specification_id else 'char',
            'help': self.description,
            'required': self.is_required,
            'label': self.ir_model_field.field_description if self.property_type == 'field' else self.description,
        }
        if self.ttype in ['many2one', 'one2many', 'many2many'] and self.property_specification_id:
            spec['spec'] = self.property_specification_id._get_specs()
        return spec

    def _process_prop_value(self, prop_value):

        # Returning empty structure if specified
        if not prop_value and self.specification_id.keep_structure and self.property_specification_id:
            return self.property_specification_id._to_empty_structure()

        # Check for empty string
        return '' if self.ttype != 'boolean' and not prop_value and self.specification_id.empty_string_for_non_bool else prop_value

    def _get_prop_value(self, record, computed_value=False):
        self.ensure_one()
        if self.property_type == 'field' or computed_value:
            field_method = '_parse_field_{}'.format(self.ttype)
            if hasattr(self, field_method):
                field_method_prop = getattr(self, field_method)
                prop_value = self._process_prop_value(field_method_prop(self.ir_model_field, record))
                return None if self.ttype != 'boolean' and not prop_value and self.specification_id.null_for_empty else prop_value
            else:
                _logger.warning("NO METHOD FOUND {}".format(field_method))
                return False if not self.specification_id.null_for_empty else None
        else:
            prop_value = self._process_prop_value(self._compute_python_code(record))
            return None if self.ttype != 'boolean' and not prop_value and self.specification_id.null_for_empty else prop_value

    def _run_property_code(self, eval_context):
        safe_eval(self.python_code.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'result'
        return eval_context.get('result')

    def _compute_python_code(self, record):
        self.ensure_one()
        eval_context = self._get_eval_context(self)
        eval_context['record'] = record
        eval_context['records'] = record
        result = False
        lang = get_lang(self.env, self.env.user.lang)
        try:
            result = self._run_property_code(eval_context)
        except Exception:
            _logger.error(traceback.format_exc())

        if self.ttype in ['many2one', 'one2many', 'many2many']:
            if result and (not hasattr(result, '_name') or getattr(result, '_name') != self.relation_model_id.model):
                raise UserError(_('Invalid return type. {} must return recordset of model {}.\nCurrent is: {}'.format(self.name, self.relation_model_id.model, result._name)))
            elif self.ttype == 'many2one':
                result = self._relation_get_value(result) if result else False
            elif self.ttype in ['one2many', 'many2many']:
                result = [self._relation_get_value(row) for row in result] if result else []
        elif self.ttype in ['date'] and not isinstance(result, str):
            result = format_date(self.env, result, lang_code=lang.code, date_format=False if not self.raw_value else DATE_FORMAT)
        elif self.ttype in ['datetime'] and not isinstance(result, str):
            tz = self.env.user.tz
            if (self.env.user._is_public()) and getattr(record, 'company_id', None) is not None:
                tz = record.company_id.tz
            result = format_datetime(self.env, result, tz=tz, lang_code=lang.code, dt_format=False if not self.raw_value else DATETIME_FORMAT)
        return result

    # Field based parsing

    def _parse_field_char(self, field, record):
        return record[field.name]

    def _parse_field_text(self, field, record):
        return record[field.name]

    def _parse_field_integer(self, field, record):
        return record[field.name]

    def _parse_field_float(self, field, record):
        return record[field.name]

    def _parse_field_boolean(self, field, record):
        return record[field.name]

    def _get_user_tz(self, record):
        tz = self.env.user.tz
        if not tz or ((self.env.user._is_public()) and getattr(record, 'company_id', None) is not None):
            tz = record.company_id.tz
        return tz

    def _parse_field_datetime(self, field, record, raw_value=False):
        datetime_obj = record[field.name]
        lang = get_lang(self.env, self.env.user.lang)
        if datetime_obj:
            tz = self._get_user_tz(record)
            if raw_value or self.raw_value:
                date_obj = datetime_obj
                if isinstance(datetime_obj, str):
                    date_obj = datetime.strptime(self._parse_field_datetime(field, record), "{} {}".format(lang.date_format, lang.time_format))
                return date_obj.strftime(DATETIME_FORMAT)
            return format_datetime(self.env, datetime_obj, tz=tz, lang_code=lang.code, dt_format=False)
        return False

    def _parse_field_date(self, field, record):
        date_obj = record[field.name]
        lang = get_lang(self.env, self.env.user.lang)
        if date_obj:
            if field.ttype == 'datetime':
                tz = self._get_user_tz(record)
                date_obj = date_obj.astimezone(timezone(tz))

            if self.raw_value:
                return date_obj.strftime(DATE_FORMAT)
            return format_date(self.env, date_obj, lang_code=lang.code, date_format=False)
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
            return self._relation_get_value(record_value)
        return False

    def _parse_field_monetary(self, field, record):
        record_value = record[field.name]

        if self.raw_value:
            return record_value

        _field = record._fields[field.name]
        currency_field = _field.currency_field or 'currency_id'
        if currency_field in record:
            return formatLang(self.env, record_value, currency_obj=record[currency_field] or self.env.company.currency_id)
        return record_value

    def _parse_field_selection(self, field, record):
        record_value = record[field.name]

        if self.raw_value:
            return record_value

        selection_dict = {}
        if record:
            selection_dict = dict(record._fields[field.name]._description_selection(self.env))
        return [record_value, selection_dict.get(record_value, record_value)]

    def _parse_field_one2many(self, field, record):
        records = record[field.name]
        if self.order_ir_field:
            records = records.sorted(self.order_ir_field, reverse=self.order_field_type == 'desc')
        return [self._relation_get_value(o2m_record) for o2m_record in records]

    def _parse_field_many2many(self, field, record):
        records = record[field.name]
        return [self._relation_get_value(m2m_record) for m2m_record in records]

    def _parse_field_html(self, field, record):
        return record[field.name]

    def _relation_get_value(self, record):
        # if self.property_specification_id and self.property_specification_id.freight_product_id:
        #     # Forcing relation record value based on defined freight product
        #     record_domain = ast.literal_eval(self.property_specification_id.freight_product_id.match_domain)
        #     record = self.env[self.relation_model_name].sudo().search(record_domain + [('id', 'in', record.ids)])
        return (self.property_specification_id and self.property_specification_id._to_dict(record)) or (record and record.display_name) or False


class ProductJsonPropertyDependency(models.Model):
    _name = 'product.json.specification.dependency'
    _description = 'JSON Specification Dependency'

    specification_id = fields.Many2one('product.json.specification', ondelete='cascade')
    name = fields.Char(required=False)
    property_id = fields.Many2one('product.json.specification.property')
    property_specification_id = fields.Many2one('product.json.specification')
