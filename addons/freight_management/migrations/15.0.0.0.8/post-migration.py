# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    customs_be_type_dict = {'ex_bond': env.ref('freight_base.custom_master_be_type_ex_bond').id,
                            'house_consumption': env.ref('freight_base.custom_master_be_type_house_consumption').id,
                            'warehouse': env.ref('freight_base.custom_master_be_type_warehouse').id
                            }
    cr.execute(""" SELECT id,customs_be_type FROM freight_house_shipment WHERE customs_be_type IS NOT NULL""")
    result = cr.fetchall()
    for rec in result:
        query = "UPDATE freight_house_shipment SET customs_be_type_id=%s WHERE id=%s" % (customs_be_type_dict[rec[1]], rec[0])
        cr.execute(query)
