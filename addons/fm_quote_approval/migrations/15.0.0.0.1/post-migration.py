# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    admin = env.ref('base.user_admin')

    cr.execute("UPDATE shipment_quote SET approving_user_id = {}".format(admin.id))
