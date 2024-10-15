from odoo import models, fields, api


class FreightCarrier(models.Model):
    _name = "freight.carrier"
    _description = "Carrier"

    name = fields.Char(required=True)
    description = fields.Text()
    email = fields.Char()
    contact_name = fields.Char(string="Carrier Contact Person")
    identifier = fields.Char(string="Carrier Identifier")
    transport_mode_id = fields.Many2one('transport.mode', required=True)
    is_sea_carrier = fields.Boolean(string="Has Sea Carrier")
    is_air_carrier = fields.Boolean(string="Has Air Carrier")
    is_road_carrier = fields.Boolean(string='Has Road Carrier')
    scac_code = fields.Char(string="SCAC Code", copy=False)
    iata_code = fields.Char(string="IATA Code", copy=False)
    airline_prefix = fields.Char(copy=False)
    logo = fields.Binary()
    partner_id = fields.Many2one('res.partner', string="Related Organization")
    active = fields.Boolean(default=True)
    carrier_agent_ids = fields.One2many('res.partner', 'freight_carrier_id', string="Carrier Agent")
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)

    _sql_constraints = [
        ('scac_code_unique', 'UNIQUE(scac_code)', "SCAC Code must be unique."),
        ('iata_code_unique', 'UNIQUE(iata_code)', "IATA Code must be unique."),
    ]

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        data = {
            'is_air_carrier': False,
            'is_sea_carrier': False,
            'is_road_carrier': False,
            'scac_code': False,
            'iata_code': False,
            'airline_prefix': False,
        }
        if self.transport_mode_id:
            transport_mode = 'road' if self.transport_mode_id.mode_type == 'land' else self.transport_mode_id.mode_type
            data.update({
                'is_{}_carrier'.format(transport_mode): True
            })
        self.update(data)

    @api.onchange('is_air_carrier')
    def _onchange_is_air_carrier(self):
        if not self.is_air_carrier:
            self.iata_code = False
            self.airline_prefix = False

    @api.onchange('is_sea_carrier')
    def _onchange_is_sea_carrier(self):
        if not self.is_sea_carrier:
            self.scac_code = False
