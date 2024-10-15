# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Code execution via query for method call to _compute_no_of_teu()
    cr.execute("""UPDATE freight_house_shipment_package package SET no_of_teu=(SELECT total_teu FROM freight_container_type WHERE id=package.container_type_id) WHERE package_mode='package'""")
    cr.execute("""UPDATE freight_master_shipment_package package SET no_of_teu=(SELECT total_teu FROM freight_container_type WHERE id=package.container_type_id) WHERE package_mode='package'""")

    cr.execute("""SELECT id from freight_house_shipment""")
    house_shipment_ids = cr.fetchall()
    count = 0
    for house_shipment_id in house_shipment_ids:
        count += 1
        cr.execute('''SELECT SUM(subquery.no_of_teu) FROM (
                   SELECT MAX(p.no_of_teu) AS no_of_teu FROM freight_house_shipment_package AS p WHERE p.shipment_id = %s GROUP BY p.container_type_id, p.container_number
                   ) AS subquery''' % (house_shipment_id[0]))
        teu_total = cr.fetchone()[0] or 0.0
        cr.execute('''UPDATE freight_house_shipment SET teu_total=%s WHERE id=%s''' % (teu_total, house_shipment_id[0]))
        _logger.info('Updating House shipment TEU {}/{}'.format(count, len(house_shipment_ids)))

    cr.execute("""SELECT id from freight_master_shipment""")
    master_shipment_ids = cr.fetchall()
    count = 0
    for master_shipment_id in master_shipment_ids:
        count += 1
        cr.execute('''SELECT SUM(subquery.no_of_teu) FROM (
                   SELECT MAX(p.no_of_teu) AS no_of_teu FROM freight_master_shipment_package AS p WHERE p.shipment_id = %s GROUP BY p.container_type_id, p.container_number
                   ) AS subquery''' % (master_shipment_id[0]))
        teu_total = cr.fetchone()[0] or 0.0
        cr.execute('''UPDATE freight_master_shipment SET teu_total=%s WHERE id=%s''' % (teu_total, master_shipment_id[0]))
        _logger.info('Updating Master shipment TEU {}/{}'.format(count, len(master_shipment_ids)))
