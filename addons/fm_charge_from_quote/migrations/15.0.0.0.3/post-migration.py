# -*- coding: utf-8 -*-


def migrate(cr, version):
    # Move shipment_cost_charge_id, shipment_revenue_charge_id columns value from M2O to M2M.

    cr.execute(""" SELECT id,shipment_cost_charge_id,shipment_revenue_charge_id FROM shipment_quote_line """)
    result = cr.fetchall()
    for rec in result:
        if rec[1] is not None:
            cost_charge_query = "INSERT INTO house_shipment_charge_cost_shipment_quote_line_rel (shipment_quote_line_id,house_shipment_charge_cost_id) VALUES(%s, %s)" % (rec[0], rec[1])
            cr.execute(cost_charge_query)
        if rec[2] is not None:
            revenue_charge_query = "INSERT INTO house_shipment_charge_revenue_shipment_quote_line_rel (shipment_quote_line_id,house_shipment_charge_revenue_id) VALUES(%s, %s)" % (rec[0], rec[2])
            cr.execute(revenue_charge_query)
