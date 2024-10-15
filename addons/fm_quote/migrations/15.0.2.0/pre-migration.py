# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    rec = env['freight.port'].search([], limit=1)

    cr.execute("UPDATE shipment_quote set port_of_loading_id = {}, port_of_discharge_id = {}".format(
        rec.id, rec.id
    ))
