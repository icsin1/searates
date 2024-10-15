# -*- coding: utf-8 -*-

from odoo.addons.web.controllers import main
from odoo.http import request


class Home(main.Home):

    # Override this to open the dashboard by default after login.
    def _login_redirect(self, uid, redirect=None):
        if not redirect and not request.env['res.users'].sudo().browse(uid).has_group('base.group_user'):
            redirect = '/dashboard'
        return super(Home, self)._login_redirect(uid, redirect=redirect)
