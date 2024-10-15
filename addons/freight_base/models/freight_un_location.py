# -*- coding: utf-8 -*-

import pytz
from odoo import models, fields, api
from odoo.addons.base.models.res_partner import _tz_get


class FreightUnLocation(models.Model):
    _name = "freight.un.location"
    _description = "UN/LOCODE Location"

    @api.model
    def set_default_timezone(self):
        return self.env.user.tz or 'UTC'

    name = fields.Char(required=True, string="Location Name")
    country_id = fields.Many2one('res.country', string='Country', required=True)
    country_state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id','=',country_id)]")
    loc_code = fields.Char(string="LOC Code", required=True, copy=False)
    sub_division = fields.Char()
    coordinates = fields.Char()
    tz = fields.Selection(_tz_get, string='Time Zone', default=set_default_timezone, required=True)
    has_rail = fields.Boolean()
    has_discharge = fields.Boolean()
    has_customs = fields.Boolean()
    has_road = fields.Boolean()
    has_seaport = fields.Boolean()
    has_store = fields.Boolean()
    has_outport = fields.Boolean()
    has_unload = fields.Boolean()
    has_airport = fields.Boolean()
    has_terminal = fields.Boolean()
    has_post = fields.Boolean()
    iata_code = fields.Char(string="IATA Code")
    port_name = fields.Char()
    air_port_name = fields.Char()
    sea_port_name = fields.Char()
    active = fields.Boolean(default=True)
    source = fields.Selection([('manual', 'Manual')], default='manual', readonly=True)

    _sql_constraints = [
        ('loc_code_unique', 'UNIQUE(loc_code)', "LOC Code must be unique.")
    ]

    @api.onchange('country_id')
    def _onchange_country_id(self):
        for rec in self:
            tz = False
            if rec.country_id and rec.country_id.code:
                tz = pytz.country_timezones.get(rec.country_id.code, ['UTC'])[0]
            rec.tz = tz

    def name_get(self):
        if not self.env.context.get('show_master_shipment') and not self.env.context.get('show_house_shipment'):
            if not self.env.context.get('show_country'):
                return super().name_get()
        result = []
        for rec in self:
            result.append((rec.id, '%s - (%s)' % (rec.name, rec.country_id.name)))
        return result
