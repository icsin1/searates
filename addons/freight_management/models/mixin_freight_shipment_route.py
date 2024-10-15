from odoo import models, fields, api, _
import json

class FreightShipmentRouteMixin(models.AbstractModel):
    _name = 'freight.shipment.route.mixin'
    _description = 'Freight Shipment Route Mixin'
    _order = 'leg_number'

    @api.depends('transport_mode_id')
    def _compute_cargo_type_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.cargo_type_domain = json.dumps(domain)

    cargo_type_domain = fields.Char(compute='_compute_cargo_type_domain', store=True)

    name = fields.Char(string="Route Desc", store=True)
    leg_number = fields.Integer(default=0)
    company_id = fields.Many2one('res.company', string='Company')
    transport_mode_id = fields.Many2one('transport.mode')
    transport_mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    is_main_carriage = fields.Boolean(default=False)
    route_type = fields.Selection([
        ('pickup', 'Pick Up'),
        ('on_carriage', 'On Carriage'),
        ('pre_carriage', 'Pre Carriage'),
        ('delivery', 'Delivery'),
        ('main_carriage', 'Main Carriage'),
        ('transshipment', 'Transshipment'),
        ('x-stuff', 'X-Stuff'),
    ])
    from_location_id = fields.Many2one('freight.un.location', string="From Location", required=True)
    to_location_id = fields.Many2one('freight.un.location', string='To Location', required=True)

    # land Transporter Details
    carrier_transport_mode = fields.Selection([
        ('truck', 'By Truck'),
        ('rail', 'By Rail')
    ], string='Carrier Mode')
    carrier_id = fields.Many2one('freight.carrier', context="{'default_is_road_carrier': True}")
    carrier_identifier = fields.Char(string='Identifier')
    carrier_driver_name = fields.Char(string='Driver Name')
    carrier_vehicle_number = fields.Char(string='Vehicle Number')
    carrier_trailer_number = fields.Char(string='Trailer Number')

    transporter_name = fields.Char(string="Transporter", compute='_onchange_set_transporter_name', store=True)
    transport_vehicle_number = fields.Char(string='Transport Identification Number', compute='_onchange_set_transport_vehicle_number', store=True)

    # Sea Vessel
    vessel_id = fields.Many2one('freight.vessel')
    obl_number = fields.Char(string='OBL Number')
    voyage_number = fields.Char('Voyage Number')

    # Air MAWB
    flight_number = fields.Char('Flight Number')
    mawb_number = fields.Char('MAWB Number')

    eta_time = fields.Datetime(string='ETA', help='Estimated Time Arrival')
    etd_time = fields.Datetime(string='ETD', help='Estimated Time Departure')
    ata_time = fields.Datetime(string='ATA', help='Actual Time Arrival')
    atd_time = fields.Datetime(string='ATD', help='Actual Time Departure')

    empty_container = fields.Char()
    empty_container_reference = fields.Char()

    remarks = fields.Text()

    @api.model
    def default_get(self, field_list):
        values = super().default_get(fields_list=field_list)
        if self._context.get('set_default_params'):
            values['route_type'] = 'pickup'
            values['carrier_transport_mode'] = 'truck'
            values['transport_mode_id'] = self.env.ref('freight_base.transport_mode_land').id
        return values

    @api.depends('carrier_transport_mode', 'transport_mode_id', 'carrier_id', 'carrier_driver_name')
    @api.onchange('carrier_transport_mode', 'transport_mode_id', 'carrier_id', 'carrier_driver_name')
    def _onchange_set_transporter_name(self):
        for rec in self:
            if rec.transport_mode_type == 'land':
                rec.transporter_name = rec.carrier_driver_name if rec.carrier_transport_mode == 'rail' else rec.carrier_id.display_name
            else:
                rec.transporter_name = rec.carrier_id.display_name

    @api.depends('transport_mode_id', 'carrier_vehicle_number', 'flight_number', 'voyage_number')
    @api.onchange('transport_mode_id', 'carrier_vehicle_number', 'flight_number', 'voyage_number')
    def _onchange_set_transport_vehicle_number(self):
        for rec in self:
            if rec.transport_mode_type == 'sea':
                rec.transport_vehicle_number = rec.voyage_number
            elif rec.transport_mode_type == 'land':
                rec.transport_vehicle_number = rec.carrier_vehicle_number
            elif rec.transport_mode_type == 'air':
                rec.transport_vehicle_number = rec.flight_number
            else:
                rec.transport_vehicle_number = False

    @api.onchange('carrier_transport_mode')
    def _onchange_carrier_transport_mode(self):
        field_lst = ['carrier_identifier', 'carrier_driver_name', 'carrier_vehicle_number',
                     'carrier_trailer_number', 'carrier_id', 'etd_time', 'eta_time',
                     'atd_time', 'ata_time', 'empty_container', 'empty_container_reference', 'remarks']
        values = {rec: False for rec in field_lst}
        self.update(values)

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode(self):
        for rec in self:
            rec.carrier_id = False

    def get_route_prefix_value(self):
        self.ensure_one()
        transport_mode_dict = {'sea': 'SH', 'land': 'RD', 'air': 'AR'}
        route_type = dict(self._fields["route_type"].selection).get(self.route_type)
        transport_mode = transport_mode_dict.get(self.transport_mode_type)
        prefix_name = '{}-{}-{}-{}-{}'.format(
            'R',
            transport_mode or '',
            route_type[0] if route_type else '',
            self.from_location_id.loc_code or '',
            self.to_location_id.loc_code or '',
        )
        return prefix_name
