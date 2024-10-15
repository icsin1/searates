# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    pro_forma_invoice_count = fields.Integer(compute='_compute_pro_forma_invoice_count', store=True)
    pro_forma_invoice_ids = fields.One2many('pro.forma.invoice', 'house_shipment_id', string='Pro Forma Invoice')

    @api.depends('pro_forma_invoice_ids')
    def _compute_pro_forma_invoice_count(self):
        for rec in self:
            rec.pro_forma_invoice_count = len(rec.pro_forma_invoice_ids)

    def action_open_pro_forma_invoice(self):
        return self.env['house.shipment.charge.revenue'].view_pro_forma_invoice(self.pro_forma_invoice_ids)
