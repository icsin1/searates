# -*- coding: utf-8 -*-


def migrate(cr, version):
    extra_cargo_types = ('cargo_type_land_bcn', 'cargo_type_land_fcl', 'cargo_type_land_lcl')
    query = "SELECT res_id from ir_model_data WHERE model='cargo.type' AND module='freight_base' AND name IN {}".format(extra_cargo_types)
    cr.execute(query)
    result = cr.fetchall()
    for rec_id in result:
        query = "UPDATE cargo_type SET active='f' WHERE id IN (%s)" % (rec_id)
        cr.execute(query)
