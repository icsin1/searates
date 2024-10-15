# -*- coding: utf-8 -*-

def migrate(cr, version):
    # Remove Master shipment & Master Shipment revenue from house shipment Revenue
    cr.execute(
        """
            UPDATE house_shipment_charge_revenue
            SET master_shipment_revenue_charge_id = Null, master_shipment_id = Null
            WHERE master_shipment_revenue_charge_id IN (SELECT id FROM master_shipment_charge_revenue WHERE house_shipment_id is not Null);
        """
    )
    # Remove Master Shipment charges which are linked with house shipment revenue.
    cr.execute(
        """
            DELETE FROM master_shipment_charge_revenue WHERE id IN (SELECT id FROM master_shipment_charge_revenue WHERE house_shipment_id is not Null);
        """
    )

    # Remove Master shipment & Master Shipment cost from house shipment cost
    cr.execute(
        """
            UPDATE house_shipment_charge_cost
            SET master_shipment_cost_charge_id = Null, master_shipment_id = Null
            WHERE master_shipment_cost_charge_id IN (SELECT id FROM master_shipment_charge_cost WHERE house_shipment_id is not Null);
        """
    )
    # Remove Master Shipment cost charges which are linked with house shipment.
    cr.execute(
        """
            DELETE FROM master_shipment_charge_cost WHERE id IN (SELECT id FROM master_shipment_charge_cost WHERE house_shipment_id is not Null);
        """
    )
