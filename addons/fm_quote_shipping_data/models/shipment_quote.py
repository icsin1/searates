from odoo import models, fields, api


class ShipmentQuote(models.Model):
    _inherit = 'shipment.quote'

    shipping_line_free_time_ids = fields.One2many('shipping.line.free.time', 'shipment_quote_id', string='Shipping Line and Free Time')
    enable_shipping_line_free_time = fields.Boolean(string='Enable Free Time', related='company_id.enable_shipping_line_free_time')

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        res = super()._onchange_transport_mode_id()
        if self.enable_shipping_line_free_time and self.transport_mode_id:
            self.create_shipping_line_and_agent()
        else:
            self.update({'shipping_line_free_time_ids': False})
        return res

    def create_shipping_line_and_agent(self):
        values = {'carrier_id': False}
        shipping_lines = []
        for val in ['shipping_line', 'agent']:
            if self.transport_mode_id.id == self.env.ref('freight_base.transport_mode_sea').id:
                free_time = 'Shipping Line'
            elif self.transport_mode_id.id == self.env.ref('freight_base.transport_mode_air').id:
                free_time = 'Air Line'
            elif self.transport_mode_id.id == self.env.ref('freight_base.transport_mode_land').id:
                free_time = 'Transporter'
            if not self.shipping_line_free_time_ids:
                if val == 'shipping_line':
                    shipping_line = self.env['shipping.line.free.time'].create({'free_time': free_time})
                    shipping_lines.append(shipping_line.id)
                else:
                    shipping_line = self.env['shipping.line.free.time'].create({'free_time': 'Agent'})
                    shipping_lines.append(shipping_line.id)
                values.update({'shipping_line_free_time_ids': shipping_lines})
            else:
                if val == 'shipping_line':
                    self.shipping_line_free_time_ids[0].free_time = free_time
        self.update(values)
