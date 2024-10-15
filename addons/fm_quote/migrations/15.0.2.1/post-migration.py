# -*- coding: utf-8 -*-


def migrate(cr, version):
    query = "UPDATE shipment_quote SET origin_un_location_id=freight_un_location.id FROM freight_un_location WHERE freight_un_location.country_id=shipment_quote.origin_country_id"
    cr.execute(query)
    query = "UPDATE shipment_quote SET destination_un_location_id=freight_un_location.id FROM freight_un_location WHERE freight_un_location.country_id=shipment_quote.destination_country_id"
    cr.execute(query)
