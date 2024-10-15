from odoo import models, fields, api


class PackageInfo(models.Model):
    _name = 'package.info'
    _description = 'Package Info'
    _order = 'name'

    name = fields.Char(string='Code', required=True)
    kind = fields.Integer(string='Kind')
    type = fields.Char(string='Type', required=True)
    material_code = fields.Char(string='Material Code')
    material = fields.Char(string='Material', required=True)
    category = fields.Char(string='Category')

    def name_get(self):
        result = []
        for package in self.sudo():
            name = '%s-%s-%s' % (package.name, package.type, package.material)
            result.append((package.id, name))
        return result
