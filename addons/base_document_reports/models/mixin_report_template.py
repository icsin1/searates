from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MixinReportTemplate(models.AbstractModel):
    _name = 'mixin.report.template'
    _inherit = ["mail.thread"]
    _description = 'Report Template Mixin'
    _template_field = None
    _report_type = None

    name = fields.Char(string='Report Name', required=True)
    res_model_id = fields.Many2one('ir.model', 'Module', required=True, ondelete='cascade')
    report_id = fields.Many2one('ir.actions.report', string='Report Action', copy=False)
    output_type = fields.Selection([], string='Output Type', required=True)
    view_type = fields.Selection([
        ('list', 'List'),
        ('form', 'Form'),
    ], default='form', string='Data Representation', required=True)
    model_name = fields.Char(string='Model Name', related='res_model_id.model', store=True)
    show_wizard = fields.Boolean(string='Show Wizard', default=False)
    sample_data_file = fields.Binary()
    terms_and_conditions = fields.Html()

    def _create_action_data(self):
        self.ensure_one()
        return {
            'binding_model_id': self.res_model_id.id,
            'model': self.model_name,
            'name': self.name,
            'binding_view_types': False if self.view_type == "both" else self.view_type,
            'show_wizard': self.show_wizard,
            'report_res_model': self._name,
            'report_res_id': self.id,
            'report_type': self._report_type
        }

    def _create_or_update_report_action(self):
        """ Method will create action if not exist or update if exist
        """
        for rec in self:
            report_name = '__dynamic__.{}'.format(rec.name.replace(' ', '_').lower())
            action_data = rec._create_action_data()
            action_data.update({'report_name': report_name})
            report = getattr(rec.report_id, rec.report_id and 'write' or 'create')(action_data)
            if isinstance(report, models.Model):
                rec.write({'report_id': report.id, 'show_wizard': report.show_wizard})

    @api.model
    def create(self, vals):
        template = super().create(vals)
        if 'report_id' not in vals:
            template._create_or_update_report_action()
        return template

    def write(self, vals):
        template = super().write(vals)
        binding_model_id = self.report_id.binding_model_id
        if 'report_id' not in vals or binding_model_id != self.res_model_id:
            self._create_or_update_report_action()
        return template

    def unlink(self):
        for template in self:
            template.report_id.unlink()
        return super().unlink()

    def init(self):
        if self._name not in ['mixin.report.template']:
            if not self._template_field:
                raise UserError(_(f"{self._name} have not implemented _template_field"))
            if not self._report_type:
                raise UserError(_(f"{self._name} have not implemented _report_type"))
        return super().init()

    def _find_template(self, record):
        """ This method is common method called from controller to render the document for defined type
        """
        self.ensure_one()
        raise NotImplementedError('_find_template() method not implemented on model {}'.format(self._name))

    def render_document_report(self, doc_ids, **kwargs):
        """ This method is common method called from controller to render the document for defined type
        """
        self.ensure_one()
        raise NotImplementedError('render_document_report() method not implemented on model {}'.format(self._name))

    def action_download_json_sample(self):
        self.ensure_one()
        action = self.env.ref('base_document_reports.sample_data_download_wizard_action').sudo().read([])[0]
        action['context'] = {
            'default_record_model': self.res_model_id.model,
            'default_report_model_id': self.res_model_id.id,
            'default_report_res_model': self._name,
            'default_report_res_id': self.id
        }
        return action

    def _get_context(self):
        return {
            'default_record_model': self.res_model_id.model,
            'default_report_model_id': self.res_model_id.id,
            'default_report_res_model': self._name,
            'default_report_res_id': self.id
        }

    def _get_template(self, record):
        return self._find_template(record)
