# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class MasterCostRevenueReport(models.Model):
    _name = "master.cost.revenue.report"
    _description = "Master Cost Revenue Report"
    _rec_name = 'product_id'
    _auto = False

    master_shipment_id = fields.Many2one('freight.master.shipment', readonly=True)
    product_id = fields.Many2one('product.product', string='Charge', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Shipment Currency', readonly=True)

    # Mapping
    revenue_line_id = fields.Many2one('master.shipment.charge.revenue', string='Revenue Mapping', readonly=True)
    cost_line_id = fields.Many2one('master.shipment.charge.cost', string='Cost Mapping', readonly=True)

    # Cost Amount
    cost_total_amount = fields.Monetary(string='Estimated Total Cost', readonly=True)
    cost_actual_total_amount = fields.Monetary('Actual Total Cost', readonly=True)
    # Revenue Amount
    revenue_total_amount = fields.Monetary(string='Estimated Total Revenue', readonly=True)
    revenue_actual_total_amount = fields.Monetary('Actual Total Revenue', readonly=True)

    estimated_margin = fields.Monetary(string='Estimated Margin', readonly=True)
    estimated_margin_percentage = fields.Float(string='Estimated Margin(%)', digits=(16, 3), readonly=True)

    actual_margin = fields.Monetary(string='Actual Margin', readonly=True)
    actual_margin_percentage = fields.Float(string='Actual Margin(%)', digits=(16, 3), readonly=True)

    _depends = {
        'master.shipment.charge.cost': [
            'master_shipment_id',
            'product_id',
            'currency_id',
            'amount_currency_id',
            'amount_conversion_rate',
            'total_amount',
            'revenue_line_id',
        ],
        'master.shipment.charge.revenue': [
            'master_shipment_id',
            'product_id',
            'currency_id',
            'amount_currency_id',
            'amount_conversion_rate',
            'amount_rate',
            'total_amount',
            'cost_line_id',
        ],
        'freight.master.shipment': [
            'revenue_charge_ids',
            'cost_charge_ids',
        ],
    }

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        query = """
            CREATE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY sub.master_shipment_id, sub.product_id) AS id,
                    sub.revenue_line_id as revenue_line_id,
                    sub.cost_line_id as cost_line_id,
                    sub.master_shipment_id as master_shipment_id,
                    sub.product_id as product_id,
                    MIN(sub.currency_id) as currency_id,

                    SUM(sub.cost_total_amount) as cost_total_amount,
                    0 as cost_actual_total_amount,

                    SUM(sub.revenue_total_amount) as revenue_total_amount,
                    0 as revenue_actual_total_amount,

                    (SUM(sub.revenue_total_amount) - SUM(sub.cost_total_amount)) as estimated_margin,
                    (((SUM(sub.revenue_total_amount) - SUM(sub.cost_total_amount)) / COALESCE(NULLIF(SUM(sub.revenue_total_amount), 0), 1)) * 100) as estimated_margin_percentage,

                    0 as actual_margin,
                    0 as actual_margin_percentage

                FROM (
                    -- Get mapped Cost-Revenue
                    SELECT
                        CL.revenue_line_id as revenue_line_id,
                        RL.cost_line_id as cost_line_id,
                        CL.master_shipment_id as master_shipment_id,
                        CL.product_id as product_id,
                        CL.currency_id as currency_id,
                        CL.total_amount as cost_total_amount,
                        RL.total_amount as revenue_total_amount
                    FROM master_shipment_charge_cost CL
                    INNER JOIN master_shipment_charge_revenue RL ON CL.revenue_line_id = RL.id

                    UNION

                    -- Get the cost
                    SELECT
                        0 as revenue_line_id,
                        CL.id as cost_line_id,
                        CL.master_shipment_id as master_shipment_id,
                        CL.product_id as product_id,
                        CL.currency_id as currency_id,
                        CL.total_amount as cost_total_amount,
                        0.0 as revenue_total_amount
                    FROM master_shipment_charge_cost as CL
                    WHERE revenue_line_id IS NULL

                    UNION

                    -- Get the revenues
                    SELECT
                        RL.id as revenue_line_id,
                        0 as cost_line_id,
                        RL.master_shipment_id as master_shipment_id,
                        RL.product_id as product_id,
                        RL.currency_id as currency_id,
                        0.0 as cost_total_amount,
                        RL.total_amount as revenue_total_amount
                    FROM master_shipment_charge_revenue as RL
                    WHERE cost_line_id IS NULL
                ) AS sub GROUP BY sub.master_shipment_id, sub.revenue_line_id, sub.cost_line_id, sub.product_id
            )
        """ % self._table
        self._cr.execute(query)
