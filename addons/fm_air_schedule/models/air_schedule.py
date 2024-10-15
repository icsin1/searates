from odoo import models, fields, api
import json


class FreightAirSchedule(models.Model):
    _inherit = 'freight.air.schedule'

    name = fields.Char(compute='_compute_name', store=True)

    @api.depends('transport_mode_id')
    def _compute_carrier_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.carrier_domain = json.dumps(domain)

    carrier_domain = fields.Char(compute='_compute_carrier_domain', store=True)

    # Cut-off
    onboarding_cut_off = fields.Datetime(help='Onboarding Cut-Off')

    parent_id = fields.Many2one('freight.air.schedule', string='Parent Schedule', ondelete='cascade')
    leg_ids = fields.One2many('freight.air.schedule', 'parent_id', string='Legs')
    flight_status = fields.Char('Flight Status')
    aircraft_type = fields.Selection([
        ('coa', 'COA'),
        ('pax', 'PAX')
    ], copy=False)

    @api.onchange('carrier_id')
    def _onchange_carrier_id(self):
        for rec in self:
            if rec.carrier_id.iata_code:
                rec.iata_number = rec.carrier_id.iata_code

    @api.depends('flight_number', 'iata_number', 'origin_port_id', 'destination_port_id')
    def _compute_name(self):
        for rec in self:
            if rec.iata_number and rec.origin_port_id and rec.destination_port_id:
                name = '{} ({} → {})'.format(rec.iata_number, rec.origin_port_id.code, rec.destination_port_id.code)
                if rec.flight_number:
                    name = '{} - {}'.format(rec.flight_number, name)
                name = name
            else:
                name = 'New Schedule'
            rec.name = name

    def action_select_schedule(self):
        self.ensure_one()
        selector_wizard_id = self.env.context.get('selector_wizard_id')
        if selector_wizard_id:
            self._on_air_schedule_selected(self.env['air.schedule.selector.wizard'].browse(selector_wizard_id), self)
        return {'type': 'ir.actions.act_window_close'}

    def _on_air_schedule_selected(self, wizard, schedule):
        pass
