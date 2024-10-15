from odoo import models, api, _


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_import_templates(self):
        return self._get_import_templates(self)

    @api.model
    def _get_import_templates(self, model):
        return [{
            'label': _('Importer Template for {}'.format(model._description)),
            'template': '/base/export/importer_file/{}'.format(model._name)
        }]
