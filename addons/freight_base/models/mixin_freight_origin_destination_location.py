from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightOriginDestinationLocationMixin(models.AbstractModel):
    _name = 'freight.origin.destination.location.mixin'
    _description = 'Freight Origin-Destination Location Mixin'

    # Locations
    origin_un_location_id = fields.Many2one('freight.un.location', string='Origin')
    origin_country_id = fields.Many2one('res.country', related='origin_un_location_id.country_id', store=True, string='Origin Country')
    destination_un_location_id = fields.Many2one('freight.un.location', string='Destination')
    destination_country_id = fields.Many2one('res.country', related='destination_un_location_id.country_id', store=True, string='Destination Country')
    origin_port_un_location_id = fields.Many2one('freight.port', string='Origin Port/Airport', domain="[('country_id', '=', origin_country_id)]")
    destination_port_un_location_id = fields.Many2one('freight.port', string='Destination Port/Airport', domain="[('country_id', '=', destination_country_id)]")

    @api.constrains('origin_port_un_location_id', 'destination_port_un_location_id')
    def _check_record_port_unique(self):
        for record in self:
            if record.origin_port_un_location_id and record.destination_port_un_location_id and \
                    record.origin_port_un_location_id.id == record.destination_port_un_location_id.id:
                raise ValidationError(_("Origin port and Destination port can't be same."))

    @api.onchange('origin_un_location_id')
    def _onchange_origin_un_location_id(self):
        is_quote_check = self.env['ir.config_parameter'].sudo().get_param('freight_management.enable_non_mandatory_fields')
        if self.origin_country_id != self.origin_port_un_location_id.country_id:
            if not is_quote_check:
                self.origin_port_un_location_id = False

    @api.onchange('destination_un_location_id')
    def _onchange_destination_un_location_id(self):
        is_quote_check = self.env['ir.config_parameter'].sudo().get_param('freight_management.enable_non_mandatory_fields')
        if self.destination_country_id != self.destination_port_un_location_id.country_id:
            if not is_quote_check:
                self.destination_port_un_location_id = False
