# -*- coding: utf-8 -*-
import logging

from odoo import fields, api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    RevenueChargeObj = env['house.shipment.charge.revenue']
    try:
        for company in env['res.company'].sudo().search([]):
            count = 0
            records = RevenueChargeObj.search([('company_id', '=', company.id), ('amount_currency_id', '!=', company.currency_id.id)], limit=50000)  # Support to migrate 50,000 records per company
            total_records = RevenueChargeObj.search_count([('company_id', '=', company.id), ('amount_currency_id', '!=', company.currency_id.id)])
            _logger.info('Executing Migration script for Company:{} Total:{} Records out of {}...'.format(company.name, len(records), total_records))
            for ids in cr.split_for_in_conditions(records.ids, size=500):
                filtered_rec = RevenueChargeObj.browse(ids)
                filtered_rec._compute_actual_invoiced_amount()
                filtered_rec._compute_residual_amount()
                filtered_rec._compute_invoice_conversion_rate()
                count += 500
                _logger.info('Executing Migration script for Record Batch - {}:{} - {}'.format(count, count + 500, fields.Datetime.now()))
                env.cr.commit()
    except Exception as e:
        _logger.warning(e)
        env.cr.commit()
