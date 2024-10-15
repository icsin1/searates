# -*- coding: utf-8 -*-

import re

from odoo import _, SUPERUSER_ID
from odoo.http import request, content_disposition
from odoo.addons.portal.controllers import portal
from odoo.exceptions import UserError


class FreightCustomerPortal(portal.CustomerPortal):

    def _generate_document_report(self, record, report_type, report_ref, download=False):

        document_type = request.env.ref(report_ref).with_user(SUPERUSER_ID)
        report_template = document_type.report_template_ref_id

        if not document_type:
            raise UserError(_("%s is not found in the system as valid document type", report_ref))

        if hasattr(record, 'company_id'):
            report_template = report_template.with_company(record.company_id)

        report = report_template.render_document_report(record.ids, model=record._name)[0]
        report_http_headers = [
            ('Content-Type', 'application/pdf' if report_type in ['pdf', 'docx'] else 'text/html'),
            ('Content-Length', len(report)),
        ]
        if report_type in ['pdf', 'docx'] and download:
            filename = "%s.pdf" % (re.sub(r'\W+', '-', record._get_report_base_filename()))
            report_http_headers.append(('Content-Disposition', content_disposition(filename)))
        return request.make_response(report, headers=report_http_headers)
