# -*- coding: utf-8 -*-
import mimetypes
import base64
from odoo import models, api, _
from odoo.tools.mimetypes import get_extension
from odoo.exceptions import ValidationError


class DocumentValidationMixin(models.AbstractModel):
    _name = 'document.validation.mixin'
    _description = 'Document Validation Mixin'

    @api.constrains('document_file')
    def _check_document_file(self):
        file_size = self.env.user.company_id.doc_file_size
        for document in self:
            if document.document_file:
                raw_data = len(base64.b64decode(document.document_file or b''))
                has_extension = get_extension(document.document_file_name) or mimetypes.guess_type(document.document_file_name)[0]
                if has_extension not in ['.docx', '.doc', '.txt', '.odt', '.xlsx', '.xls', '.jpeg', '.png', '.pdf', '.jpg']:
                    raise ValidationError(_('Allowed Format docx, doc, txt, odt, xlsx, xls, jpeg, png, pdf, jpg'))
                if raw_data > (file_size * 1024 * 1024):
                    raise ValidationError(_('Upload file can be allowed less then {} MB'.format(file_size)))
