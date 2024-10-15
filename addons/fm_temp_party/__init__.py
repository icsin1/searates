from . import models
from odoo import api, SUPERUSER_ID


def _fm_temp_party_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    company_obj = env['res.company'].sudo()
    opportunity_obj = env['crm.prospect.opportunity']
    quote_obj = env['shipment.quote']
    house_shipment_obj = env['freight.house.shipment']
    service_job_obj = env['freight.service.job']
    for company in company_obj.search([]):
        for opp in opportunity_obj.search([('company_id', '=', company.id)]):
            temp_party_address = '{}-{}'.format(opp.street1 or '', opp.street2 or '')
            if opp.opportunity_type == 'new':
                temp_party_name = opp.prospect_id and opp.prospect_id.name
            else:
                temp_party_name = opp.partner_id and opp.partner_id.name
            query = ("UPDATE crm_prospect_opportunity SET temp_party_name='%s',temp_party_address='%s' WHERE id IN (%s)"
                     % (temp_party_name, temp_party_address, opp.id))
            cr.execute(query)
        for quote in quote_obj.search([('company_id', '=', company.id)]):
            query = ("UPDATE shipment_quote SET temp_shipper_name='%s' ,temp_shipper_address='%s' ,"
                     "temp_consignee_name='%s' ,temp_consignee_address='%s' WHERE id IN (%s)"
                     % (quote.shipper_id.name or '', quote.shipper_address_id.name or '',
                        quote.consignee_id.name or '', quote.consignee_address_id.name or '', quote.id))
            cr.execute(query)
        for house_shipment in house_shipment_obj.search([('company_id', '=', company.id)]):
            query = ("UPDATE freight_house_shipment SET temp_shipper_name='%s' ,temp_shipper_address='%s' ,"
                     "temp_consignee_name='%s' ,temp_consignee_address='%s' WHERE id IN (%s)"
                     % (house_shipment.shipper_id.name or '', house_shipment.shipper_address_id.name or '',
                        house_shipment.consignee_id.name or '', house_shipment.consignee_address_id.name or '', house_shipment.id))
            cr.execute(query)
        for service_job in service_job_obj.search([('company_id', '=', company.id)]):
            query = ("UPDATE freight_service_job SET temp_shipper_name='%s' ,temp_shipper_address='%s' ,"
                     "temp_consignee_name='%s' ,temp_consignee_address='%s' WHERE id IN (%s)"
                     % (service_job.shipper_id.name or '', service_job.shipper_address_id.name or '',
                        service_job.consignee_id.name or '', service_job.consignee_address_id.name or '', service_job.id))
            cr.execute(query)
