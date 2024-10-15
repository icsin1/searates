# -*- coding: utf-8 -*-

from odoo.addons.web.controllers.main import Database
from odoo.http import request, ALLOWED_DEBUG_MODES
from odoo import http


class CustomDatabase(Database):

    def _render_template(self, **d):
        # Call the parent class's _render_template method to get the initial content
        """ Inherit method for change image from odoo to searates """
        content = super(CustomDatabase, self)._render_template(**d)
        content = content.replace("Odoo", "SearatesERP")
        content = content.replace("web/static/img/favicon.ico", "odoo_base/static/src/images/favicon.ico")
        content = content.replace("web/static/img/logo2.png", "odoo_base/static/src/images/searateserp-logo.png")
        return content

    @http.route()
    def manager(self, **kw):
        """ Inherit method for bypass this url if debug is off. """
        request._cr = None
        if 'debug' in request.httprequest.args:
            for debug in request.httprequest.args['debug'].split(','):
                if debug in ALLOWED_DEBUG_MODES:
                    return super(CustomDatabase, self).manager(**kw)
                else:
                    return request.redirect('/web')
        else:
            return request.redirect('/web')
