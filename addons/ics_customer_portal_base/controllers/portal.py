# -*- coding: utf-8 -*-
from odoo.http import Controller, route, request


class CustomerPortal(Controller):

    @route(['/dashboard'], type='http', auth="user", website=True)
    def dashboard_home(self, **kw):
        return request.render("ics_customer_portal_base.dashboard", {})
