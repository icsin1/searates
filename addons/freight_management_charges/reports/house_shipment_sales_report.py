# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class OperationSaleReport(models.Model):
    _name = "house.shipment.sales.report"
    _description = "House Shipment Sales Report"
    _rec_name = 'partner_id'
    _auto = False

    shipment_id = fields.Many2one('freight.house.shipment', readonly=True)
    shipment_date = fields.Date(related='shipment_id.shipment_date', readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)

    house_id = fields.Many2one('freight.house.shipment', readonly=True)
    shipping_line_id = fields.Many2one('freight.carrier', readonly=True)

    # Revenue & cost Amount
    revenue_amount = fields.Monetary(string='Sales', readonly=True)
    cost_amount = fields.Monetary(string='Costs', readonly=True)
    received_amount = fields.Monetary(string='Received Amount', readonly=True)
    invoiced_amount = fields.Monetary(string='Invoiced Amount', readonly=True)

    _depends = {
        'house.shipment.charge.revenue': [
            'house_shipment_id',
            'partner_id',
            'currency_id',
            'company_id',
            'amount_currency_id',
            'amount_conversion_rate',
            'total_amount',
            'cost_line_id',
            'invoice_received_amount',
            'invoiced_amount'
        ],
        'house.shipment.charge.cost': [
            'house_shipment_id',
            'partner_id',
            'currency_id',
            'company_id',
            'amount_currency_id',
            'amount_conversion_rate',
            'total_amount',
            'revenue_line_id',
        ],
        'freight.house.shipment': [
            'name',
            'shipment_date',
            'revenue_charge_ids',
            'cost_charge_ids',
            'client_id',
            'shipper_id',
            'consignee_id'
        ],
    }

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        query = """
            CREATE VIEW %s AS (
                -- Mapped lines
                    SELECT
                        ROW_NUMBER() OVER (ORDER BY RL.partner_id) AS id,
                        RL.partner_id as partner_id,
                        HS.shipping_line_id as shipping_line_id,
                        RL.house_shipment_id as shipment_id,
                        HS.company_id as company_id,
                        SUM(RL.total_amount) as revenue_amount,
                        SUM(CL.total_amount) as cost_amount,
                        SUM(RL.invoiced_amount) as invoiced_amount,
                        SUM(RL.invoice_received_amount) as received_amount
                    FROM house_shipment_charge_revenue as RL
                    JOIN house_shipment_charge_cost as CL ON CL.house_shipment_id = RL.house_shipment_id and RL.cost_line_id = CL.id
                    JOIN freight_house_shipment as HS ON HS.id = RL.house_shipment_id
                    GROUP BY RL.partner_id, HS.shipping_line_id, RL.house_shipment_id, RL.cost_line_id, HS.company_id

                    UNION

                -- Getting all the costs without mapping

                    SELECT
                        ROW_NUMBER() OVER (ORDER BY HS.client_id) AS id,
                        HS.client_id as partner_id,
                        HS.shipping_line_id as shipping_line_id,
                        CL.house_shipment_id as shipment_id,
                        HS.company_id as company_id,
                        0.0 as revenue_amount,
                        SUM(CL.total_amount) as cost_amount,
                        0.0 as invoiced_amount,
                        0.0 as received_amount
                    FROM house_shipment_charge_cost as CL
                    JOIN freight_house_shipment as HS ON HS.id = CL.house_shipment_id
                    WHERE CL.revenue_line_id is NULL
                    GROUP BY HS.client_id, HS.shipping_line_id, CL.house_shipment_id, HS.company_id

                    UNION

                -- Getting all the revenue without mapping

                    SELECT
                        ROW_NUMBER() OVER (ORDER BY RL.partner_id) AS id,
                        RL.partner_id as partner_id,
                        HS.shipping_line_id as shipping_line_id,
                        RL.house_shipment_id as shipment_id,
                        HS.company_id as company_id,
                        SUM(RL.total_amount) as revenue_amount,
                        0.0 as cost_amount,
                        SUM(RL.invoiced_amount) as invoiced_amount,
                        SUM(RL.invoice_received_amount) as received_amount
                    FROM house_shipment_charge_revenue as RL
                    JOIN freight_house_shipment as HS ON HS.id = RL.house_shipment_id
                    WHERE RL.cost_line_id is NULL
                    GROUP BY RL.partner_id, HS.shipping_line_id, RL.house_shipment_id, HS.company_id
            )
        """ % self._table
        self._cr.execute(query)
