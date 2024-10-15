# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID, Command


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for group_xml in ['odoo_base.group_odoo_all_menu_access', 'odoo_base.group_freight_technical_support_team']:
        group = env.ref(group_xml, False)
        group.users.write({'groups_id': [Command.unlink(group.id)]})
