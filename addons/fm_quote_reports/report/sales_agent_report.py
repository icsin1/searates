# -*- coding: utf-8 -*-

from odoo import models, api


class SalesAgentReport(models.AbstractModel):
    _name = 'report.fm_quote_reports.report_sales_agent'
    _description = 'Sales Agent Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        ctx = data.get('context')
        active_id = ctx.get('active_id')
        docs = self.env['wiz.sales.agent.report'].browse(active_id)

        domain = [('status_change_date', '>=', docs.from_date),
                  ('status_change_date', '<=', docs.to_date),
                  ('status', '=', docs.quote_status),
                  ('quote_id.user_id', 'in', docs.sales_agent_ids.ids)]
        shipment_quote_history = docs.env['shipment.quote.status.history'].sudo().search(domain)
        shipment_quote = shipment_quote_history.mapped('quote_id')
        quote_list = []
        user_list = []
        for quote in shipment_quote:
            shipment_history = quote.status_history_ids.sudo().search([
                ('status_change_date', '>=', docs.from_date), ('status_change_date', '<=', docs.to_date), ('status', '=', docs.quote_status),
                ('quote_id.user_id', 'in', docs.sales_agent_ids.ids), ('quote_id', '=', quote.id)], limit=1)
            status = dict(shipment_history._fields['status'].selection).get(shipment_history.status)
            if not shipment_history:
                continue
            if quote.user_id.id in user_list:
                quote_list.append({'date': shipment_history.status_change_date.date(), 'name': quote.name,
                                   'customer': quote.client_id.name, 'user_name': quote.user_id.id, 'status': status,
                                   'estimated_total_revenue': quote.estimated_total_revenue, 'estimated_total_cost': quote.estimated_total_cost, 'estimated_profit': quote.estimated_profit})
            else:
                user_list.append(quote.user_id.id)
                quote_list.append({'date': shipment_history.status_change_date.date(), 'name': quote.name,
                                   'customer': quote.client_id.name,
                                   'user_name': quote.user_id.id,
                                   'status': status,
                                   'estimated_total_revenue': quote.estimated_total_revenue,
                                   'estimated_total_cost': quote.estimated_total_cost,
                                   'estimated_profit': quote.estimated_profit})

        data['quote_list'] = quote_list
        data['users_name'] = user_list
        data['remarks'] = docs.remarks

        return {
            'doc_ids': docs.ids,
            'doc_model': 'wiz.sales.agent.report',
            'data': data,
            'docs': docs,
        }
