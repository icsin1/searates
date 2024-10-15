# -*- coding: utf-8 -*-

from odoo import fields, models, _


class FreightQuoteDocument(models.Model):
    _name = 'freight.quote.document'
    _inherit = ['freight.document.mixin', 'document.validation.mixin']
    _description = 'Freight Quote Document'

    quote_id = fields.Many2one('shipment.quote', string='Quote', required=True, ondelete='cascade')

    def action_download_report(self, context={}):
        context.update({'active_ids': self.quote_id.ids})
        return super().action_download_report(context)

    def action_send_by_email(self):
        return self.generate_send_by_email_action(
            self.quote_id.name,
            self.quote_id.ids,
            self.quote_id.client_id.ids
        )

    def action_doc_version_history(self):
        self.ensure_one()
        return {
            'name': _('Document Version History'),
            'type': 'ir.actions.act_window',
            'res_model': 'doc.version.history',
            'view_mode': 'tree',
            'target': 'new',
            'context': {'create': False},
            'domain': [('res_id', '=', self.id), ('res_model', '=', 'freight.quote.document')]
        }
