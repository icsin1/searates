
import logging
from odoo import api, fields, models, modules

_logger = logging.getLogger(__name__)

FIELDS_BLACKLIST = [
    "id",
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
    "display_name",
    "__last_update",
]

MODEL_BLACKLIST = [
    'ir.audit.log.operation',
    'ir.audit.log.action',
    'ir.audit.log.auth',
    'bus.presence',
    'res.users.log'
]

EMPTY_DICT = {}


class DictDiffer(object):
    """Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """

    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current = set(current_dict)
        self.set_past = set(past_dict)
        self.intersect = self.set_current.intersection(self.set_past)

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        return {o for o in self.intersect if self.past_dict[o] != self.current_dict[o]}

    def unchanged(self):
        return {o for o in self.intersect if self.past_dict[o] == self.current_dict[o]}


class Models(models.Model):
    _inherit = "ir.model"

    log_operation = fields.Boolean('Log Operation', default=True)

    def _register_hook(self):
        """Get all rules and apply them to log method calls."""
        super(Models, self)._register_hook()
        if not hasattr(self.pool, "_auditlog_field_cache"):
            self.pool._auditlog_field_cache = {}
        if not hasattr(self.pool, "_auditlog_model_cache"):
            self.pool._auditlog_model_cache = {}
        if not self:
            self = self.sudo().search([("log_operation", "=", True)])
        return self._patch_methods()

    def _patch_methods(self):
        """Patch ORM methods of models defined in rules to log their calls."""
        updated = False
        model_cache = self.pool._auditlog_model_cache
        for model in self.filtered(lambda mdl: mdl.log_operation and self.pool.get(mdl.model)):
            model_cache[model.model] = model.id
            model_model = self.env[model.model]
            if not hasattr(model_model, '_ignore_audit'):
                if model_model._auto and not model_model._transient:
                    check_attr = "auditlog_ruled_create"
                    if not hasattr(model_model, check_attr):
                        model_model._patch_method("create", model._make_create())
                        setattr(type(model_model), check_attr, True)
                        updated = True
                    check_attr = "auditlog_ruled_write"
                    if not hasattr(model_model, check_attr):
                        model_model._patch_method("write", model._make_write())
                        setattr(type(model_model), check_attr, True)
                        updated = True
                    check_attr = "auditlog_ruled_unlink"
                    if not hasattr(model_model, check_attr):
                        model_model._patch_method("unlink", model._make_unlink())
                        setattr(type(model_model), check_attr, True)
                        updated = True
            else:
                model.write({'log_operation': False})
                _logger.info(f"Ignored audit log patch_methods for {model.model} through attributes")
        return updated

    def _revert_methods(self):
        updated = False
        for model in self:
            model_model = self.env[model.model]
            for method in ["create", "read", "write", "unlink"]:
                if getattr(model, "log_%s" % method) and hasattr(getattr(model_model, method), "origin"):
                    model_model._revert_method(method)
                    delattr(type(model_model), "auditlog_ruled_%s" % method)
                    updated = True
        if updated:
            modules.registry.Registry(self.env.cr.dbname).signal_changes()

    @api.model
    def create(self, vals):
        new_record = super().create(vals)
        if new_record._register_hook():
            modules.registry.Registry(self.env.cr.dbname).signal_changes()
        return new_record

    @api.model
    def _get_auditlog_fields(self, model):
        return list(name for name, field in model._fields.items() if (not field.compute and not field.related) or field.store)

    def _make_create(self):
        self.ensure_one()

        @api.model_create_multi
        @api.returns("self", lambda value: value.id)
        def create_full(self, vals_list, **kwargs):
            self = self.with_context(auditlog_disabled=True)
            new_records = create_full.origin(self, vals_list, **kwargs)

            if self._name in MODEL_BLACKLIST:
                return new_records

            model_obj = self.env["ir.model"].sudo().search([('model', '=', self._name), ('log_operation', '=', True)], limit=1)
            if not model_obj:
                return new_records

            fields_list = model_obj._get_auditlog_fields(self)

            new_values = {}
            for new_record in new_records.sudo():
                new_values.setdefault(new_record.id, {})
                for fname, field in new_record._fields.items():
                    if fname in fields_list:
                        new_values[new_record.id][fname] = field.convert_to_read(new_record[fname], new_record)

            # Creating Logs
            model_obj._create_audit_logs(self.env.uid, self._name, new_records.ids, "create", None, new_values)

            # Returning Records
            return new_records
        return create_full

    def _make_write(self):
        self.ensure_one()

        def write_full(self, vals, **kwargs):
            self = self.with_context(auditlog_disabled=True)
            model_obj = self.env["ir.model"].sudo().search([('model', '=', self._name), ('log_operation', '=', True)], limit=1)

            if self._name in MODEL_BLACKLIST or not model_obj:
                return write_full.origin(self, vals, **kwargs)

            fields_list = model_obj._get_auditlog_fields(self)

            # Storing Old Values
            old_values = {d["id"]: d for d in self.sudo().with_context(prefetch_fields=False).read(fields_list)}
            # Executing Origin Method
            result = write_full.origin(self, vals, **kwargs)
            # Getting New Values
            new_values = {d["id"]: d for d in self.sudo().with_context(prefetch_fields=False).read(fields_list)}

            # Creating Write Log
            model_obj.sudo()._create_audit_logs(self.env.uid, self._name, self.ids, "write", old_values, new_values)

            return result
        return write_full

    def _make_unlink(self):
        self.ensure_one()

        def unlink_full(self, **kwargs):
            self = self.with_context(auditlog_disabled=True)
            model_obj = self.env["ir.model"].sudo().search([('model', '=', self._name), ('log_operation', '=', True)], limit=1)

            if self._name in MODEL_BLACKLIST or not model_obj:
                return unlink_full.origin(self, **kwargs)

            fields_list = model_obj._get_auditlog_fields(self)
            old_values = {d["id"]: d for d in self.sudo().with_context(prefetch_fields=False).read(fields_list)}

            # Creating Log for Unlink
            model_obj.sudo()._create_audit_logs(self.env.uid, self._name, self.ids, "unlink", old_values, None)
            return unlink_full.origin(self, **kwargs)

        return unlink_full

    def _json_to_table(self, json_data):
        # Start building the HTML table
        html_table = "<table class=\"table table-sm table-striped table-bordered\">\n"

        if json_data:
            # Extract column headers from the keys of the first dictionary in the JSON data
            headers = json_data[0].keys()

            # Construct the header row
            html_table += "<tr>"
            for header in headers:
                html_table += f"<th>{header}</th>"
            html_table += "</tr>\n"

            # Construct the data rows
            for row in json_data:
                html_table += "<tr>"
                for header in headers:
                    html_table += f"<td>{row.get(header, '')}</td>"
                html_table += "</tr>\n"

        # End the table
        html_table += "</table>"

        return html_table

    def _create_audit_logs(self, uid, res_model, res_ids, method, old_values=None, new_values=None, additional_log_values=None):
        old_values = old_values or EMPTY_DICT
        new_values = new_values or EMPTY_DICT

        if not old_values and not new_values:
            return

        log_model = self.env["ir.audit.log.operation"].sudo()
        model_model = self.env[res_model].sudo()

        model_id = self.pool._auditlog_model_cache[res_model]

        for res_id in res_ids:
            names = model_model.browse(res_id).name_get()
            res_name = names and names[0] and names[0][1]
            vals = {
                "name": res_name,
                "res_model": model_id,
                "model_id": model_id,
                "res_id": res_id,
                "operation_type": method,
                "user_id": uid,
            }
            vals.update(additional_log_values or {})

            if isinstance(new_values, dict) and isinstance(old_values, dict):
                diff = DictDiffer(new_values.get(res_id, EMPTY_DICT), old_values.get(res_id, EMPTY_DICT))

                if method == "create":
                    new_values = self._create_log_line_on_create(self, res_id, diff.added(), new_values)
                    if new_values:
                        html_values = self._json_to_table(new_values)
                        vals.update({'change_values': html_values})
                elif method == "write":
                    log_vals = self._create_log_line_on_write(self, res_id, diff.changed(), old_values, new_values)
                    if log_vals:
                        vals.update({'change_values': self._json_to_table(log_vals)})
                elif method == "unlink":
                    old_values = self._create_log_line_on_read(self, res_id, list(old_values.get(res_id, EMPTY_DICT).keys()), old_values)
                    if old_values:
                        vals.update({'change_values': self._json_to_table(old_values)})

            # Creating Log only if there is value
            if vals.get('change_values'):
                log_model.create(vals)

    def _get_field(self, model, field_name):
        cache = self.pool._auditlog_field_cache
        if field_name not in cache.get(model.model, {}):
            cache.setdefault(model.model, {})
            field_model = self.env["ir.model.fields"].sudo()
            all_model_ids = [model.id]
            all_model_ids.extend(model.inherited_model_ids.ids)
            field = field_model.search(
                [("model_id", "in", all_model_ids), ("name", "=", field_name)]
            )
            if not field:
                cache[model.model][field_name] = False
            else:
                field_data = field.read(load="_classic_write")[0]
                cache[model.model][field_name] = field_data
        return cache[model.model][field_name]

    def _create_log_line_on_create(self, model, res_id, fields_list, new_values, fields_to_exclude=[]):
        """Log field filled on a 'create' operation."""
        log_vals_create = []
        fields_to_exclude = (fields_to_exclude or []) + FIELDS_BLACKLIST
        for field_name in fields_list:
            if field_name in fields_to_exclude:
                continue
            field = self._get_field(model, field_name)
            # not all fields have an ir.models.field entry (ie. related fields)
            if field:
                log_vals = self._prepare_log_line_vals_on_create(res_id, field, new_values)
                log_vals_create.append(log_vals)
        return log_vals_create

    def _prepare_log_line_vals_on_create(self, res_id, field, new_values):
        vals = {
            "Field Name": "{} ({})".format(field["field_description"], field['name']),
            "New Value": new_values[res_id][field["name"]],
        }
        if field["relation"] and "2many" in field["ttype"]:
            new_value_text = (self.env[field["relation"]].browse(vals["New Value"]).name_get())
            vals["New Value Text"] = new_value_text
        return vals

    def _create_log_line_on_read(self, model, res_id, fields_list, read_values, fields_to_exclude=[]):
        """Log field filled on a 'read' operation."""
        log_vals_read = []

        fields_to_exclude = (fields_to_exclude or []) + FIELDS_BLACKLIST
        for field_name in fields_list:
            if field_name in fields_to_exclude:
                continue
            field = self._get_field(model, field_name)
            if field:
                log_vals = self._prepare_log_line_vals_on_read(res_id, field, read_values)
                log_vals_read.append(log_vals)
        return log_vals_read

    def _prepare_log_line_vals_on_read(self, res_id, field, read_values):
        vals = {
            "Field Name": "{} ({})".format(field["field_description"], field['name']),
            "Old Value": read_values[res_id][field["name"]],
        }
        if vals.get('Old value') and field["relation"] and "2many" in field["ttype"]:
            old_value_text = (self.env[field["relation"]].browse(vals["Old Value"]).name_get())
            vals["Old Value Text"] = old_value_text
        return vals

    def _create_log_line_on_write(self, model, res_id, fields_list, old_values, new_values, fields_to_exclude=[]):
        log_vals_write = []
        """Log field updated on a 'write' operation."""
        fields_to_exclude = (fields_to_exclude or []) + FIELDS_BLACKLIST
        for field_name in fields_list:

            if field_name in fields_to_exclude:
                continue
            field = self._get_field(model, field_name)
            if field:
                log_vals = self._prepare_log_line_vals_on_write(res_id, field, old_values, new_values)
                log_vals_write.append(log_vals)
        return log_vals_write

    def _prepare_log_line_vals_on_write(self, res_id, field, old_values, new_values):
        vals = {
            "Field Name": "{} ({})".format(field["field_description"], field['name']),
            "Old Value": str(old_values[res_id][field["name"]]),
            "New Value": str(new_values[res_id][field["name"]]),
        }
        return vals

    @api.model
    def _update_vals_list(self, vals_list):
        for vals in vals_list:
            for fieldname, fieldvalue in vals.items():
                if isinstance(fieldvalue, models.BaseModel) and not fieldvalue:
                    vals[fieldname] = False
        return vals_list
