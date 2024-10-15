from odoo import models, fields, api


class ShipmentProfitabilityMixin(models.AbstractModel):
    _name = 'shipment.profitability.mixin'
    _description = 'Shipment Profitability Mixin'

    currency_id = fields.Many2one('res.currency')

    # Estimated Amounts
    estimated_revenue = fields.Monetary(string='Estimated Revenue')
    estimated_cost = fields.Monetary(string='Estimated Cost')
    estimated_margin = fields.Monetary(string='Estimated Margin (Amt)', compute='_compute_estimated_margin', store=True)
    estimated_margin_percentage = fields.Float(string='Estimated Margin(%)', compute='_compute_estimated_margin_percentage', store=True)

    # Received Amounts
    received_revenue = fields.Monetary(string='Revenue Received')
    paid_cost = fields.Monetary(string='Cost Paid')
    received_margin = fields.Monetary(string='Received Margin', compute='_compute_received_margin', store=True)
    received_margin_percentage = fields.Float(string='Received Margin(%)', compute='_compute_received_margin_percentage', store=True)

    # Due Amount
    due_revenue = fields.Monetary(string='Due Revenue', compute='_compute_due_revenue_amount', store=True)
    due_cost = fields.Monetary(string='Due Cost', compute='_compute_due_cost_amount', store=True)

    @api.depends('estimated_cost', 'estimated_revenue')
    def _compute_estimated_margin(self):
        for shipment in self:
            shipment.estimated_margin = shipment.estimated_revenue - shipment.estimated_cost

    @api.depends('estimated_margin', 'estimated_revenue')
    def _compute_estimated_margin_percentage(self):
        for shipment in self:
            if shipment.estimated_revenue <= 0:
                shipment.estimated_margin_percentage = 0.0
            else:
                shipment.estimated_margin_percentage = (shipment.estimated_margin * 100) / shipment.estimated_revenue

    @api.depends('received_revenue', 'paid_cost')
    def _compute_received_margin(self):
        for shipment in self:
            shipment.received_margin = (shipment.received_revenue - shipment.paid_cost)

    @api.depends('received_margin', 'received_revenue')
    def _compute_received_margin_percentage(self):
        for shipment in self:
            if shipment.received_revenue <= 0:
                shipment.received_margin_percentage = 0.0
            else:
                shipment.received_margin_percentage = (shipment.received_margin * 100) / shipment.received_revenue

    @api.depends('received_revenue', 'estimated_revenue')
    def _compute_due_revenue_amount(self):
        for shipment in self:
            shipment.due_revenue = (shipment.estimated_revenue - shipment.received_revenue)

    @api.depends('paid_cost', 'estimated_cost')
    def _compute_due_cost_amount(self):
        for shipment in self:
            shipment.due_cost = (shipment.estimated_cost - shipment.paid_cost)
