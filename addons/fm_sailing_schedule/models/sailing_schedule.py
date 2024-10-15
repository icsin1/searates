from odoo import models, fields, api, _
from odoo.exceptions import ValidationError



class FreightSailingSchedule(models.Model):
    _inherit = 'freight.schedule'

    name = fields.Char(compute='_compute_name', store=True)

    # Vessel and Carrier Details
    scac_number = fields.Char(string='SCAC Number', help='Standard Carrier Alpha Code (SCAC)')
    imo_number = fields.Char(related='vessel_id.imo_number', string='IMO Number', help='International Maritime Organization (IMO)')
    service_name = fields.Char('Service Name')
    voyage_number = fields.Char('Voyage Number', copy=False)

    # Cut-off
    vessel_cut_off = fields.Datetime(help='Vessel/Terminal Cut-Off')
    vgm_cut_off = fields.Datetime(help='Verified Gross Mass Cut-Off')

    parent_id = fields.Many2one('freight.schedule', string='Parent Schedule', ondelete='cascade')
    leg_ids = fields.One2many('freight.schedule', 'parent_id', string='Legs')

    @api.constrains('voyage_number')
    def _check_unique_voyage_number(self):
        for rec in self:
            if self.search_count([('id', '!=', rec.id), ('voyage_number', 'ilike', rec.voyage_number)]) > 0:
                raise ValidationError(_('Voyage Number must be unique.'))

    @api.constrains('estimated_departure_date', 'vessel_cut_off')
    def _check_sailing_schedule_etd_vessel_cut_off(self):
        for rec in self:
            if rec.estimated_departure_date and rec.vessel_cut_off and (rec.vessel_cut_off > rec.estimated_departure_date):
                raise ValidationError(_(
                    'The vessel cut off date should not be greater than ETD date.'))

    @api.onchange('carrier_id')
    def _onchange_carrier_id(self):
        for rec in self:
            if rec.carrier_id.scac_code:
                rec.scac_number = rec.carrier_id.scac_code

    @api.depends('voyage_number', 'scac_number', 'origin_country_id', 'destination_country_id')
    def _compute_name(self):
        for rec in self:
            if rec.scac_number and rec.origin_country_id and rec.destination_country_id:
                name = '{} ({} → {})'.format(rec.scac_number, rec.origin_country_id.code, rec.destination_country_id.code)
                if rec.voyage_number:
                    name = '[{}] {}'.format(rec.voyage_number, name)
                rec.name = name
            else:
                rec.name = 'New Schedule'

    def action_select_schedule(self):
        self.ensure_one()
        selector_wizard_id = self.env.context.get('selector_wizard_id')
        if selector_wizard_id:
            self._on_sailing_schedule_selected(self.env['sailing.schedule.selector.wizard'].browse(selector_wizard_id), self)
        return {'type': 'ir.actions.act_window_close'}

    def _on_sailing_schedule_selected(self, wizard, schedule):
        pass
