# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    rec = env['freight.port'].create({'name': 'Dummy', 'code': 'DUMMY', 'country_id': env.ref('base.in').id})

    cr.execute("UPDATE crm_prospect_lead set port_of_loading_id = {}, port_of_discharge_id = {}".format(
        rec.id, rec.id
    ))
    cr.execute("UPDATE crm_prospect_opportunity set port_of_loading_id = {}, port_of_discharge_id = {}".format(
        rec.id, rec.id
    ))
