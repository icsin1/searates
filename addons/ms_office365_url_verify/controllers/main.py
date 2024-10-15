# -*- coding: utf-8 -*-

import base64
from odoo import http
from odoo.http import request


class MicrosoftOffice365VerifierController(http.Controller):

    def _get_office35_verifier_file(self, filename):
        files = request.env['res.company'].sudo().search([
            ('office365_url_verifier_file', '!=', False),
            ('office365_url_verifier_filename', '=', filename)
        ], limit=1)
        if files:
            return base64.b64decode(files.office365_url_verifier_file).decode('utf-8')
        return '{}'

    @http.route('/ms<office35_verifier>.txt', type='http', auth='public')
    def microsoft_office35_verifier(self, office35_verifier, **kwargs):
        filename = 'ms%s.txt' % (office35_verifier)
        verifier_file = self._get_office35_verifier_file(filename)
        return request.make_response(verifier_file, [
            ('Content-Type', 'text/plain'),
            ('Content-Length', len(verifier_file))
        ])
