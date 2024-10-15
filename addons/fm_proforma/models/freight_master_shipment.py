# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FreightMasterShipment(models.Model):
    _inherit = 'freight.master.shipment'

    house_shipment_proforma_count = fields.Integer(compute='_compute_house_shipment_proforma_count')

    @api.depends('house_shipment_ids')
    def _compute_house_shipment_proforma_count(self):
        for rec in self:
            rec.house_shipment_proforma_count = len(rec.house_shipment_ids.mapped('pro_forma_invoice_ids'))

    def action_open_proforma_invoices(self):
        pro_forma_invoice_ids = self.house_shipment_ids.pro_forma_invoice_ids
        action = self.env['house.shipment.charge.revenue'].view_pro_forma_invoice(pro_forma_invoice_ids)
        return action
