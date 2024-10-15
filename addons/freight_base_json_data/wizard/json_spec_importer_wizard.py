import base64
import logging
import json
import traceback
from odoo import models, fields, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class JsonSpecImporterWizard(models.TransientModel):
    _name = 'json.spec.importer.wizard'
    _description = 'JSON Spec Importer Wizard'

    json_exported_file = fields.Binary()

    def _find_model(self, model_name):
        model_obj = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
        if not model_obj:
            raise ValidationError(_('Unable to find model {}'.format(model_name)))
        return model_obj

    def _find_model_field(self, model_name, field_name):
        model_field_obj = self.env['ir.model.fields'].search([('name', '=', field_name), ('model_id.model', '=', model_name)], limit=1)
        if not model_field_obj:
            raise ValidationError(_("Unable to find find field '{}' number model '{}'".format(field_name, model_name)))
        return model_field_obj

    def _create_spec(self, json_spec, data_keys):

        # Creating dependency first
        for dependency in json_spec.get('dependencies', []):
            spec_xml_id, spec_obj = self._create_spec(dependency, data_keys)
            data_keys['specification_key_{}'.format(dependency.get('specification_key'))] = spec_obj.id
            # Forcing commit
            self._cr.commit()

        xml_id = 'json_spec_key_{}'.format(json_spec.get('specification_key'))
        json_spec_obj = self.env.ref('__import__.{}'.format(xml_id), raise_if_not_found=False)

        replace_ids = []
        noupdate_properties = self.env['product.json.specification.property']
        if json_spec_obj:
            noupdate_properties = json_spec_obj.property_ids.filtered(lambda prop: prop.noupdate)
            replace_ids = noupdate_properties.ids

        values = {
            'name': json_spec.get('name'),
            'model_id': self._find_model(json_spec.get('model')).id,
            'product_domain': json_spec.get('product_domain', '[]'),
            'empty_string_for_non_bool': json_spec.get('empty_string_for_non_bool'),
            'keep_structure': json_spec.get('keep_structure'),
            'description': json_spec.get('description'),
            'json_type': json_spec.get('json_type', 'general'),
            'property_ids': [(6, False, replace_ids)] + [(0, 0, {
                'name': prop.get('name'),
                'property_type': prop.get('property_type'),
                'model_id': self._find_model(prop.get('model_name')).id,
                'ir_model_field': self._find_model_field(prop.get('model_name'), prop.get('ir_model_field_name')).id if prop.get('ir_model_field_name') else False,
                'relation_model_id': self._find_model(prop.get('relation_model_name')).id if prop.get('relation_model_name') else False,
                'ttype': prop.get('ttype'),
                'is_required': prop.get('is_required'),
                'description': prop.get('description'),
                'python_code': prop.get('python_code'),
                'property_specification_id': data_keys.get('specification_key_{}'.format(prop.get('property_specification_key')))
            }) for prop in json_spec.get('properties') if prop.get('name') not in noupdate_properties.mapped('name')]
        }

        if json_spec_obj:
            # Updating existing json spec
            json_spec_obj.write(values)
            return '__import__.{}'.format(xml_id), json_spec_obj

        # Creating specification
        JSONSpec = self.env['product.json.specification']

        spec = JSONSpec.create(values)
        # Generating XML ID
        existing_xml_data = self.env.ref('__import__.{}'.format(xml_id), raise_if_not_found=False)
        if not existing_xml_data:
            self.env['ir.model.data'].create({
                'module': '__import__',
                'name': xml_id,
                'model': JSONSpec._name,
                'res_id': spec.id
            })
        return '__import__.{}'.format(xml_id), spec

    def action_import_spec(self):
        self.ensure_one()
        try:
            json_payload = json.loads(base64.b64decode(self.json_exported_file.decode('utf-8')))
            data_keys = {}
            xml_id, json_spec_obj = self._create_spec(json_payload, data_keys)
            self.notify_user(_('JSON Specification Import DONE'), _('JSON Specification with Sub Dependent specification imported'), 'success')
            return {'type': 'ir.actions.act_window_close'}
        except Exception as e:
            _logger.error(traceback.print_exc())
            raise ValidationError(_(str(e)))
