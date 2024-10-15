from odoo import models, fields, api


class DocVersionHistory(models.Model):
    _name = 'doc.version.history'
    _description = 'Document Version History'
    _rec_name = 'filename'
    _order = 'upload_time DESC'

    user_id = fields.Many2one('res.users', string='By User', default=lambda self: self.env.user)
    upload_time = fields.Datetime(string="Uploaded On", copy=False, default=lambda self: fields.Datetime.now())
    filename = fields.Char(string='Filename')
    description = fields.Char(string='Description')
    upload_file = fields.Binary(string='File', required=True)
    res_model = fields.Char('Related Document Model Name')
    res_id = fields.Many2oneReference('Related Document ID', model_field='res_model')

    @api.model_create_single
    def create(self, vals):
        res = super().create(vals)
        res.unlink_documents()
        return res

    def write(self, vals):
        res = super().write(vals)
        for job in self:
            job.unlink_documents()
        return res

    def unlink_documents(self):
        doc_ids = self.search([
            ('id', '!=', self.id),
            ('res_id', '=', self.res_id),
            ('res_model', '=', self.res_model)
        ])
        max_document_history = int(self.env['ir.config_parameter'].sudo().get_param('freight_base.max_document_history') or 1) - 1
        if len(doc_ids) >= max_document_history:
            doc_ids.sorted('upload_time', reverse=True)[max_document_history:].unlink()
