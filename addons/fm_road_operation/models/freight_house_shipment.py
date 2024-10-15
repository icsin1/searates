
from odoo import models, fields, api, _
from odoo.addons.freight_management.models.freight_house_shipment import HOUSE_STATE
from odoo.exceptions import ValidationError

HOUSE_STATE.insert(3, ('hlr_generated', 'HLR Generated'))


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

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

    export_road_state = fields.Selection(related="state", string="Export Road State")
    transportation_detail_ids = fields.One2many('freight.shipment.transportation.details', 'house_shipment_id',
                                                string="Transportation Detail")
    pickup_country_id = fields.Many2one('res.country', string='Pickup Country', readonly=False,
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
    road_origin_un_location_id = fields.Many2one('freight.un.location', related="origin_un_location_id", readonly=False, string="Pickup Location")
    road_destination_un_location_id = fields.Many2one('freight.un.location', related="destination_un_location_id", string="Delivery Location", readonly=False)
    pickup_zipcode = fields.Char()
    delivery_zipcode = fields.Char()
    truck_count = fields.Integer(compute='_compute_house_shipment_truck_count', store=True)

    @api.constrains('etp_time', 'etd_time')
    def _check_shipment_eta_etd_time(self):
        for shipment in self:
            if shipment.etp_time and shipment.etd_time and (shipment.etp_time > shipment.etd_time):
                raise ValidationError(_(
                    'Estimated pickup date should be less than estimated delivery date.'))

    @api.constrains('apt_time', 'atd_time')
    def _check_shipment_ata_atd_time(self):
        for shipment in self:
            if shipment.apt_time and shipment.atd_time and (shipment.apt_time > shipment.atd_time):
                raise ValidationError(_(
                    'Actual pickup date should be less than actual delivery date.'))

    @api.constrains('origin_un_location_id', 'destination_un_location_id')
    def _check_road_pickup_destination(self):
        for shipment in self.filtered(lambda ship: ship.origin_un_location_id and ship.destination_un_location_id):
            if shipment.origin_un_location_id.id == shipment.destination_un_location_id.id:
                raise ValidationError(_("Pickup and Delivery location can't be same."))

    @api.onchange('pickup_country_id')
    def _onchange_pickup_country_id(self):
        if self.shipment_quote_id and self.shipment_quote_id.origin_country_id.id != self.pickup_country_id.id or not self.shipment_quote_id:
            self.pickup_location_type_id = False
            self.origin_un_location_id = False

    @api.onchange('pickup_location_type_id')
    def _onchange_pickup_location_type_id(self):
        if self.shipment_quote_id and self.shipment_quote_id.pickup_location_type_id != self.pickup_location_type_id or not self.shipment_quote_id:
            self.origin_un_location_id = False

    @api.onchange('delivery_country_id')
    def _onchange_delivery_country_id(self):
        if self.shipment_quote_id and self.shipment_quote_id.destination_country_id.id != self.delivery_country_id.id or not self.shipment_quote_id:
            self.delivery_location_type_id = False
            self.destination_un_location_id = False

    @api.onchange('delivery_location_type_id')
    def _onchange_delivery_location_type_id(self):
        if self.shipment_quote_id and self.shipment_quote_id.delivery_location_type_id != self.delivery_location_type_id or not self.shipment_quote_id:
            self.destination_un_location_id = False

    def action_change_status(self):
        action = super().action_change_status()
        if self.mode_type == "land" and self.shipment_type_key == 'export':
            if 'default_export_state' in action['context']:
                del action['context']['default_export_state']  # Road Freight HLR Generated state not found in export_state, so deleted it from context
            action['context']['default_road_export_state'] = self.state
        return action

    def action_attach_shipment_house(self):
        super().action_attach_shipment_house()
        for shipment in self:
            if shipment.mode_type == "land":
                shipment.transportation_detail_ids.write({
                    'master_shipment_id': shipment.parent_id,
                })

    def action_create_master_shipment(self):
        self.ensure_one()
        res = super().action_create_master_shipment()
        context = dict(res.get('context') or {})
        context.update({
            'default_pickup_country_id': self.pickup_country_id.id,
            'default_delivery_country_id': self.delivery_country_id.id,
            'default_pickup_zipcode': self.pickup_zipcode,
            'default_delivery_zipcode': self.delivery_zipcode,
            'default_etp_time': self.etp_time,
            'default_apt_time': self.apt_time,
        })
        res['context'] = context
        return res

    @api.depends('transportation_detail_ids')
    def _compute_house_shipment_truck_count(self):
        for shipment in self:
            shipment.truck_count = len(shipment.transportation_detail_ids) if shipment.mode_type == 'land' else 0
