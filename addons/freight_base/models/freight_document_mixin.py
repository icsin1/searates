# -*- coding: utf-8 -*-
import base64
from odoo import models, fields, _
from odoo.exceptions import UserError


class FreightDocumentMixin(models.AbstractModel):
    _name = 'freight.document.mixin'
    _description = 'Freight Document Mixin'
    _order = "datetime desc"

    name = fields.Char(string='Description', required=True)
    document_type_id = fields.Many2one('freight.document.type', string='Document Type', required=True)
    report_action_id = fields.Many2one('ir.actions.report', related='document_type_id.report_action_id', store=True)
    document_mode = fields.Selection(related="document_type_id.document_mode", store=True)
    document_file = fields.Binary(string='Document')
    document_file_name = fields.Char(string='File Name')
    datetime = fields.Datetime(string='DateTime', required=True, default=fields.Datetime.now)

    def write(self, vals):
        document = super(FreightDocumentMixin, self).write(vals)
        for doc in self:
            if vals and vals.get('document_file'):
                self.env['doc.version.history'].sudo().create({
                    'upload_file': doc.document_file,
                    'filename': doc.document_file_name,
                    'description': doc.document_type_id.name,
                    'res_id': doc,
                    'res_model': doc._name
                })
        return document

    def action_download_report(self, context={}):
        self.ensure_one()
        if self.report_action_id:
            action = self.report_action_id.read()[0]
            action['context'] = {**action.get('context', {}), **context}
            return action
        return False

    def generate_send_by_email_action(self, record_name, doc_ids, partner_ids, context={}):
        self.ensure_one()
        attachment_data = {}
        kwargs = {}
        if self.document_mode == 'in':
            if not self.document_file:
                raise UserError(_('No Document uploaded. Upload document to send an email.'))
            attachment_data.update({
                'datas': self.document_file,
                'name': "{}_{}".format(record_name, self.document_file_name)
            })
        else:
            if not self.document_type_id or not self.document_type_id.report_template_ref_id:
                raise UserError(_('No Document type selected. select document to send an email.'))

            report_template = self.document_type_id.report_template_ref_id

            attachment_data.update({
                'datas': base64.encodebytes(report_template.render_document_report(doc_ids, **kwargs)[0]),
                'name': "{}_{}".format(self.document_type_id.name, record_name)
            })

        attachment = self.env['ir.attachment'].create({
            'type': 'binary',
            'name': self.name,
            'res_model': 'mail.compose.message',
            **attachment_data
        })
        ctx = {
            'default_model': self._name,
            'default_res_id': self.id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_light",
            "default_partner_ids": partner_ids,
            "default_attachment_ids": attachment.ids,
            'force_email': True,
            'mark_quote_as_sent': True,
        }
        return {
            'name': _('Send Mail'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
