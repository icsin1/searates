from odoo import models, fields


class AccountEDIDocument(models.Model):
    _inherit = 'account.edi.document'

    state = fields.Selection(selection_add=[('fail', 'Failed')], ondelete={'fail': 'cascade'})

    def _process_documents_status_check_web_services(self):
        for edi_format in self.mapped('edi_format_id'):
            docs = self.filtered(lambda dc: dc.edi_format_id == edi_format)
            edi_format._post_invoice_status_check(docs, docs.mapped('move_id'))
