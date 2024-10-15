from odoo import models, fields, api


class FreightCustomLocation(models.Model):
    _name = 'freight.custom.location'
    _description = 'Custom Location'

    name = fields.Char('Custom Location', required=True)
    city_id = fields.Many2one('res.city', domain='[("country_id", "=", country_id)]')
    state_id = fields.Many2one('res.country.state', domain='[("country_id", "=", country_id)]')
    country_id = fields.Many2one('res.country')

    @api.onchange('state_id')
    def _onchange_state_id(self):
        for rec in self:
            if rec.state_id:
                self.country_id = rec.state_id.country_id
