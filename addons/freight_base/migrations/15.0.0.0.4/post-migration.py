# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    air_mode = env.ref('freight_base.transport_mode_air')
    sea_mode = env.ref('freight_base.transport_mode_sea')
    land_mode = env.ref('freight_base.transport_mode_land')

    allowed_route_modes = {
        air_mode.id: [air_mode.id, land_mode.id],
        sea_mode.id: [sea_mode.id, land_mode.id],
        land_mode.id: [air_mode.id, sea_mode.id, land_mode.id],
    }

    for mode_id in allowed_route_modes:
        for allowed_mode_id in allowed_route_modes[mode_id]:
            query = "INSERT INTO route_transport_mode_rel(transport_mode_id,route_transport_mode_id) VALUES(%s, %s)" % (mode_id, allowed_mode_id)
            cr.execute(query)
