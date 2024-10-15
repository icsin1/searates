
from odoo import models, fields, _


class FreightServiceJobDocument(models.Model):
    _name = 'freight.service.job.document'
    _inherit = ['freight.document.mixin', 'document.validation.mixin']
    _description = 'Freight Service Job Document'

    service_job_id = fields.Many2one('freight.service.job', required=True, ondelete='cascade')

    def action_download_report(self, context={}):
        context.update({'active_ids': self.service_job_id.ids})
        return super().action_download_report(context)

    def action_doc_version_history(self):
        self.ensure_one()
        return {
            'name': _('Document Version History'),
            'type': 'ir.actions.act_window',
            'res_model': 'doc.version.history',
            'view_mode': 'tree',
            'target': 'new',
            'context': {'create': False},
            'domain': [('res_id', '=', self.id), ('res_model', '=', 'freight.service.job.document')]
        }

    def action_send_by_email(self):
        return self.generate_send_by_email_action(
            self.service_job_id.name,
            self.service_job_id.ids,
            self.service_job_id.client_id.ids
        )
