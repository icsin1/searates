from odoo import models, fields, api, _
from lxml import etree
from odoo.exceptions import ValidationError


class View(models.Model):
    _inherit = "ir.ui.view"

    user_id = fields.Many2one('res.users')
    is_custom = fields.Boolean()
    original_view_id = fields.Integer()

    @api.model
    def _get_inheriting_views_domain(self):
        return super()._get_inheriting_views_domain() + [
            '|',
            ('is_custom', '=', False),
            '&',
            '&',
            ('is_custom', '=', True),
            ('user_id', '=', self.env.user.id if self.env.company.view_customization in ['all', 'admin_only'] else False),
            ('original_view_id', 'in', self._context.get('original_view_id')),
        ]

    def _get_combined_arch(self):
        return super(View, self.with_context(original_view_id=self.ids))._get_combined_arch()


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def extend_view(self, view_fields, view_id, original_view_id, fields_to_reuse={}, add_new_fields=True, recursive=True, first_call=False):
        is_allowed = (self.env.company.view_customization in ('admin', 'admin_only') and self.env.is_admin()) or self.env.company.view_customization == 'all'
        if not is_allowed:
            return
        self = self.sudo()

        if first_call:
            if len(view_fields) == 0:
                raise ValidationError(_('You need to select at least one field.'))
            self.unlink_views(view_id)
        view = self.env['ir.ui.view'].browse(view_id)
        for children_id in view.inherit_children_ids.filtered(lambda x: not x.is_custom):
            self.extend_view(view_fields, children_id.id, original_view_id, fields_to_reuse, False, False)
        if recursive and view.inherit_id.filtered(lambda x: not x.is_custom):
            self.extend_view(view_fields, view.inherit_id.id, original_view_id, fields_to_reuse, False)
            for children_id in view.inherit_id.inherit_children_ids.filtered(lambda x: not x.is_custom):
                self.extend_view(view_fields, children_id.id, original_view_id, fields_to_reuse, False, False)

        data = etree.Element('data')
        fields = list(map(lambda x: x.get('name'), view_fields))
        repeated_fields = {}
        for field in [elem for elem in etree.fromstring(view.arch).findall('.//field') if 'position' not in elem.attrib]:
            xpath = etree.SubElement(data, 'xpath')
            if field.get('name') not in repeated_fields:
                xpath.set('expr', f'//field[@name="{field.get("name")}"]')
                repeated_fields[field.get('name')] = 1
            else:
                count = repeated_fields[field.get('name')]
                xpath.set('expr', f'//field[@name="{field.get("name")}"][{count}]')
                repeated_fields[field.get('name')] = count + 1

            xpath.set('position', 'attributes')
            attribute = etree.SubElement(xpath, 'attribute')
            attribute.set('name', 'invisible')
            attribute.text = '1'
            if field.get('name') in fields:
                if field.get('name') not in fields_to_reuse:
                    fields_to_reuse[field.get('name')] = field
                else:
                    field_str = f"{field.get('name')}_{repeated_fields[field.get('name')]}"
                    fields_to_reuse[field_str] = field

        if add_new_fields:
            xpath = etree.SubElement(data, 'xpath')
            xpath.set('expr', '//tree//field[last()]')
            xpath.set('position', 'after')
            for field_name in view_fields:
                if field_name.get('name') in fields_to_reuse:
                    field = fields_to_reuse.pop(field_name.get('name'))
                    if 'optional' in field.attrib:
                        field.attrib.pop('optional')
                    xpath.append(field)
                    field_str = f"{field.get('name')}_{repeated_fields.get(field.get('name'))}"
                    if field_str in fields_to_reuse:
                        field = fields_to_reuse.pop(field_str)
                        if 'invisible' in field.attrib and field.attrib['invisible'] != 1:
                            if 'optional' in field.attrib:
                                field.attrib.pop('optional')
                            xpath.append(field)
                else:
                    etree.SubElement(xpath, 'field').set('name', field_name.get('name'))

        if len(list(data.iter())) > 1:
            self.env['ir.ui.view'].create({
                'type': view.type,
                'model': view.model,
                'inherit_id': view.id,
                'user_id': self.env.user.id if self.env.company.view_customization in ['all', 'admin_only'] else False,
                'is_custom': True,
                'mode': 'extension',
                'original_view_id': original_view_id,
                'arch': etree.tostring(data, pretty_print=True),
                'name': f'web_customization: {self.env.user.display_name}: {view.name}'
            })

    def get_top_level_view(self, view):
        if view.inherit_id:
            return self.get_top_level_view(view.inherit_id)
        return view

    def unlink_child_views(self, view):
        for view in view.inherit_children_ids.filtered_domain(view._get_inheriting_views_domain()):
            self.unlink_child_views(view)
            if view.is_custom:
                view.unlink()

    @api.model
    def unlink_views(self, view_id):
        view = self.env['ir.ui.view'].with_context(original_view_id=[view_id]).browse(view_id)
        self.unlink_child_views(self.get_top_level_view(view))
