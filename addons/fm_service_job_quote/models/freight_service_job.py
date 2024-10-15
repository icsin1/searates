# -*- coding: utf-8 -*-

from odoo import fields, models


class FreightServiceJob(models.Model):
    _inherit = 'freight.service.job'

    service_job_quote_id = fields.Many2one('shipment.quote')

    def action_shipment_sevice_quote(self):
        self.ensure_one()
        return {
            'name': 'Quotes',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shipment.quote',
            'res_id': self.service_job_quote_id.id,
        }
