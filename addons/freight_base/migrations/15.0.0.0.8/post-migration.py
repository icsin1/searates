# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    sea_transport_mode_id = env.ref('freight_base.transport_mode_sea', raise_if_not_found=False)
    if sea_transport_mode_id:
        env['freight.container.type'].write({'transport_mode_id': sea_transport_mode_id.id})
