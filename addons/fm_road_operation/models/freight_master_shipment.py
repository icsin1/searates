from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class FreightMasterShipment(models.Model):
    _inherit = 'freight.master.shipment'

    road_state = fields.Selection(related="state", string="Export Road State")
    truck_count = fields.Integer(compute='_compute_master_shipment_truck_count', store=True)

    def action_change_status(self):
        action = super().action_change_status()
        if self.mode_type == "land":
            action['context']['default_road_state'] = self.road_state
        return action

    @api.depends('etp_time', 'etd_time')
    def _compute_transit_time(self):
        for rec in self:
            transit_time = 0
            if rec.etd_time and rec.etp_time:
                transit_time = (rec.etd_time - rec.etp_time).days
            rec.transit_time = transit_time

    def _inverse_pickup_country_id(self):
        for shipment in self:
            shipment.origin_country_id = shipment.pickup_country_id

    def _inverse_delivery_country_id(self):
        for shipment in self:
            shipment.destination_country_id = shipment.delivery_country_id

    pickup_country_id = fields.Many2one('res.country', string='Pickup Country ', readonly=False,
                                        inverse="_inverse_pickup_country_id", store=True)
    delivery_country_id = fields.Many2one('res.country', string='Delivery Country', readonly=False,
                                          inverse="_inverse_delivery_country_id", store=True)
    pickup_location_type_id = fields.Many2one('freight.location.type', string="Pickup Location Type")
    delivery_location_type_id = fields.Many2one('freight.location.type', string="Delivery Location Type")
    etp_time = fields.Datetime("ETP")
    apt_time = fields.Datetime("ATP")
    etd_time = fields.Datetime("ETD")
    atd_time = fields.Datetime("ATD")
    transit_time = fields.Integer('TT(In days)', compute='_compute_transit_time', store=True)
    transportation_detail_ids = fields.One2many('freight.shipment.transportation.details', 'master_shipment_id',
                                                string="Transportation Detail")
    road_origin_un_location_id = fields.Many2one('freight.un.location', related="origin_un_location_id", readonly=False, string="Pickup Location")
    road_destination_un_location_id = fields.Many2one('freight.un.location', related="destination_un_location_id", string="Delivery Location ", readonly=False)
    pickup_zipcode = fields.Char()
    delivery_zipcode = fields.Char()

    @api.onchange('pickup_country_id')
    def _onchange_pickup_country_id(self):
        if self.is_direct_shipment and self.house_shipment_ids:
            values = {}
            house_shipment = self.house_shipment_ids[0]
            fields_lst = ['pickup_location_type_id', 'origin_un_location_id']
            if house_shipment.transport_mode_id.id != self.transport_mode_id.id or not house_shipment:
                values = {field: False for field in fields_lst}
                self.update(values)
            else:
                values = {field: house_shipment[field] for field in fields_lst}
                self.update(values)

    @api.onchange('pickup_location_type_id')
    def _onchange_pickup_location_type_id(self):
        if self.is_direct_shipment and self.house_shipment_ids:
            values = {}
            house_shipment = self.house_shipment_ids[0]
            fields_lst = ['origin_un_location_id']
            if house_shipment.transport_mode_id.id != self.transport_mode_id.id or not house_shipment:
                values = {field: False for field in fields_lst}
                self.update(values)
            else:
                values = {field: house_shipment[field] for field in fields_lst}
                self.update(values)

    @api.onchange('delivery_country_id')
    def _onchange_delivery_country_id(self):
        if self.is_direct_shipment and self.house_shipment_ids:
            values = {}
            house_shipment = self.house_shipment_ids[0]
            fields_lst = ['delivery_location_type_id', 'destination_un_location_id']
            if house_shipment.transport_mode_id.id != self.transport_mode_id.id or not house_shipment:
                values = {field: False for field in fields_lst}
                self.update(values)
            else:
                values = {field: house_shipment[field] for field in fields_lst}
                self.update(values)

    @api.onchange('delivery_location_type_id')
    def _onchange_delivery_location_type_id(self):
        if self.is_direct_shipment and self.house_shipment_ids:
            values = {}
            house_shipment = self.house_shipment_ids[0]
            fields_lst = ['destination_un_location_id']
            if house_shipment.transport_mode_id.id != self.transport_mode_id.id or not house_shipment:
                values = {field: False for field in fields_lst}
                self.update(values)
            else:
                values = {field: house_shipment[field] for field in fields_lst}
                self.update(values)

    @api.constrains('road_origin_un_location_id', 'road_destination_un_location_id')
    def _check_origin_destination_un_location(self):
        for rec in self.filtered(lambda shipment: shipment.mode_type == 'land'):
            if rec.road_origin_un_location_id and rec.road_destination_un_location_id and rec.road_origin_un_location_id == rec.road_destination_un_location_id:
                raise ValidationError(_('Pickup and Delivery location Can not be same.'))

    def get_shipment_house_domain(self):
        if self.mode_type == "land":
            domain = [
                ('state', '!=', 'cancelled'),
                ('parent_id', '=', False),
                ('transport_mode_id', '=', self.transport_mode_id.id),
                ('shipment_type_id', '=', self.shipment_type_id.id),
                ('cargo_type_id', '=', self.cargo_type_id.id),
                ('pickup_location_type_id', '=', self.pickup_location_type_id.id),
                ('origin_un_location_id', '=', self.origin_un_location_id.id),
                ('delivery_location_type_id', '=', self.delivery_location_type_id.id),
                ('destination_un_location_id', '=', self.destination_un_location_id.id),
                ('company_id', '=', self.company_id.id),
            ]
            return domain
        else:
            return super().get_shipment_house_domain()

    def action_fetch_transportation_details_from_house(self):
        self.ensure_one()
        transportation_detail_ids = self.house_shipment_ids.mapped('transportation_detail_ids').filtered(lambda t: not t.master_shipment_id)
        if transportation_detail_ids:
            transportation_detail_ids.write({
                'master_shipment_id': self.id,
            })

    @api.model
    def get_transporter_booking(self, domain=[], limit=10, offset=0, **kwargs):
        self = self.with_context(**kwargs.get('context', {}))
        tableData = []
        ShipmentObj = self.env['freight.master.shipment']
        carrier = ShipmentObj.search(domain).mapped('transportation_detail_ids.carrier_id')
        carrier_data = carrier.read_group([('id', 'in', carrier.ids)], ['name'], ['name'],  offset=offset, lazy=False)
        for line in carrier_data:
            line_values = {'Transporter': line['name'] and line['name'] or 'Not Available'}
            line_values['Total'] = ShipmentObj.search_count(expression.AND([domain, [('transportation_detail_ids.carrier_id.name', '=', line['name'])]]))
            tableData.append(line_values)
            tableData.sort(key=lambda x: x['Total'], reverse=True)
        return tableData[offset: limit]

    @api.depends('transportation_detail_ids')
    def _compute_master_shipment_truck_count(self):
        for ms_shipment in self:
            ms_shipment.truck_count = len(ms_shipment.transportation_detail_ids) if ms_shipment.mode_type == 'land' else 0
