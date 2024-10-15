# -*- coding: utf-8 -*-

from odoo import models, api, _
import base64


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self, vals):
        file_size = self.env.user.company_id.doc_file_size or 5
        if 'datas' in vals:
            if vals.get('res_model') in ['freight.house.shipment', 'freight.master.shipment']:
                uploaded_file_size = len(base64.b64decode(vals.get('datas') or b''))
                if uploaded_file_size > file_size * 1024 * 1024:
                    vals.update({
                        'datas': b'',
                        'description': 'Uploaded file is too large.'
                    })
        return super(IrAttachment, self).create(vals)
