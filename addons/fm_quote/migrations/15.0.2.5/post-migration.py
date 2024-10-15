# -*- coding: utf-8 -*-

def migrate(cr, version):
    # Move Cargo type column value from M2O to M2M.

    cr.execute(""" SELECT id,cargo_type_id FROM shipment_quote_template """)
    result = cr.fetchall()
    for rec in result:
        query = "INSERT INTO quote_template_cargo_type_rel (quote_template_id,cargo_type_id) VALUES(%s, %s)" % (rec[0], rec[1])
        cr.execute(query)
