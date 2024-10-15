# -*- coding: utf-8 -*-

from odoo import fields, models, api


class FreightVessel(models.Model):
    _name = "freight.vessel"
    _description = 'Freight Vessel'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Vessel Name', required=True)
    carrier_id = fields.Many2one('freight.carrier', domain="[('transport_mode_id.mode_type', '=', 'sea')]", required=True)
    imo_number = fields.Char(string='IMO Number')
    mmsi_number = fields.Char(string='MMSI Number', help="Maritime Mobile Service Identity")
    category_id = fields.Many2one('freight.vessel.category', string='Vessel Type')
    country_id = fields.Many2one('res.country', string='Country')

    @api.depends("name", "code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[{}] {}'.format(rec.code, rec.name)
