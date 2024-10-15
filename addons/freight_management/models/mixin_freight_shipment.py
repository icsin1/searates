from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json


class FreightShipmentMixin(models.AbstractModel):
    _name = 'freight.shipment.mixin'
    _description = 'Freight Shipment Mixin'
    _inherit = [
        'mail.thread', 'mail.activity.mixin',
        'freight.base.company.user.mixin', 'freight.departure.arrival.mixin', 'freight.origin.destination.location.mixin', 'freight.product.mixin', 'freight.cargo.weight.volume.mixin',
    ]
    _order = 'create_date DESC'

    @api.depends('transport_mode_id')
    def _compute_shipping_line_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.shipping_line_domain = json.dumps(domain)

    # IATA Code will be fetched from current company
    def _get_default_iata_code(self):
        return self.env.company.agent_iata_code

    shipping_line_domain = fields.Char(compute='_compute_shipping_line_domain', store=True)

    # Base Company & User Details
    sales_agent_id = fields.Many2one('res.users', domain="[('company_id', '=', company_id)]", string="Sales Agent", required=True,
                                     default=lambda self: self.env.user, tracking=True)

    # Shipment details
    is_direct_shipment = fields.Boolean(string='Direct Shipment', copy=False)
    shipment_date = fields.Date(required=True)

    # Transport Details
    shipment_type_key = fields.Char(compute='_compute_shipment_type_key', store=True)
    service_mode_id = fields.Many2one('freight.service.mode')

    # Ext. carrier Booking details
    carrier_booking_reference_number = fields.Char(string='MBL', copy=False)
    carrier_booking_carrier_number = fields.Char(string='Carrier Number', copy=False)
    carrier_booking_reference_agent = fields.Char(string='Booking Reference Agent')
    carrier_forwarder_reference_number = fields.Char('Forwarder Reference Number', copy=False)
    carrier_vessel_cut_off_datetime = fields.Datetime(string='Vessel Cut-Off Datetime', copy=False)
    carrier_vgm_cut_off_datetime = fields.Datetime('VGM Cut-Off Datetime', help="Verified Gross Mass Cut-Off Datetime", copy=False)
    carrier_warehouse_cut_off_datetime = fields.Datetime('Warehouse Cut-Off Datetime', copy=False)
    aircraft_type = fields.Selection(selection=[('pax', 'Passenger Cargo Aircraft (PAX)'), ('cao', 'Cargo Aircraft Only (COA)')], copy=False)

    # cargo weight and volume
    auto_update_weight_volume = fields.Boolean('Auto Update Weight & Volume')
    gross_weight_unit = fields.Float('Gross Weight', default=None, compute='_compute_auto_weight_volume', store=True)
    gross_weight_unit_uom_id = fields.Many2one('uom.uom', compute='_compute_auto_weight_volume', store=True)
    weight_volume_unit = fields.Float('Volumetric Weight', default=None, compute='_compute_auto_weight_volume', store=True)
    weight_volume_unit_uom_id = fields.Many2one('uom.uom', compute='_compute_auto_weight_volume', store=True)

    # Carrier information
    voyage_number = fields.Char(string='Voyage No', copy=False)
    vessel_id = fields.Many2one('freight.vessel', string='Vessel', copy=False)
    shipping_line_id = fields.Many2one('freight.carrier', string='Shipping Line', copy=False)

    # Locations
    origin_port_un_location_id = fields.Many2one('freight.port', domain="[('country_id', '=', origin_country_id), ('transport_mode_id', '=', transport_mode_id)]", string='Origin Port/Airport')
    destination_port_un_location_id = fields.Many2one(
        'freight.port', domain="[('country_id', '=', destination_country_id), ('transport_mode_id', '=', transport_mode_id)]", string='Destination Port/Airport')
    origin_port_name = fields.Char(related='origin_port_un_location_id.name', store=True)
    destination_port_name = fields.Char(related='destination_port_un_location_id.name', store=True, string='Destination Port')
    is_courier_shipment = fields.Boolean(string='Courier Shipment')
    teu_total = fields.Integer(string='TEUs', compute='_compute_teu_total', store=True)

    # Other Related Information
    handling_info = fields.Char(string='Handling Information', copy=False)
    accounting_info = fields.Char(string='Accounting Information', copy=False)
    commodity = fields.Text(string='Commodity', copy=False)
    iata_rate = fields.Monetary(string='IATA Rate', currency_field='iata_rate_currency_id', tracking=True)
    iata_rate_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id, tracking=True)
    iata_code = fields.Char(string='IATA Code', readonly=True, default=_get_default_iata_code)
    declared_value_carrier = fields.Char(string='Declared Value for Carrier', copy=False)
    declared_value_customer = fields.Char(string='Declared Value for Customs', copy=False)

    @api.depends(
        'auto_update_weight_volume',
        'cargo_is_package_group'
    )
    def _compute_auto_weight_volume(self):
        for shipment in self:
            shipment.gross_weight_unit = shipment.gross_weight_unit
            shipment.weight_volume_unit = shipment.weight_volume_unit
            shipment.gross_weight_unit_uom_id = shipment.gross_weight_unit_uom_id
            shipment.weight_volume_unit_uom_id = shipment.weight_volume_unit_uom_id

    @api.depends('shipment_type_id')
    def _compute_shipment_type_key(self):
        for rec in self:
            if rec.shipment_type_id == self.env.ref('freight_base.shipment_type_import'):
                rec.shipment_type_key = 'import'
            elif rec.shipment_type_id == self.env.ref('freight_base.shipment_type_export'):
                rec.shipment_type_key = 'export'
            elif rec.shipment_type_id == self.env.ref('freight_base.shipment_type_cross_trade'):
                rec.shipment_type_key = 'cross'
            elif rec.shipment_type_id == self.env.ref('freight_base.shipment_type_domestic'):
                rec.shipment_type_key = 'domestic_export'
            elif rec.shipment_type_id == self.env.ref('freight_base.shipment_type_reexport'):
                rec.shipment_type_key = 're_export'
            else:
                rec.shipment_type_key = False

    @api.depends('packaging_mode', 'container_ids', 'package_ids')
    def _compute_teu_total(self):
        for shipment in self:
            if shipment.packaging_mode == 'container':
                shipment.teu_total = sum(shipment.mapped('container_ids.no_of_teu'))
            else:
                # For package mode - Consider TEU sum for Unique containerNumber + Container Type Entry
                unique_combinations = {(record.container_type_id.id, record.container_number.container_number): record.no_of_teu for record in shipment.package_ids}
                total_teu_sum = sum(unique_combinations.values())
                shipment.teu_total = total_teu_sum

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        fields_lst = ['cargo_type_id', 'origin_port_un_location_id', 'destination_port_un_location_id', 'shipping_line_id']
        values = {field: False for field in fields_lst}
        self.update(values)

    @api.onchange('is_courier_shipment')
    def _onchange_is_courier_shipment(self):
        if not self._origin and self.is_courier_shipment != self.env.context.get('default_is_courier_shipment'):
            self.shipment_type_id = False
            self.transport_mode_id = False

    @api.constrains('is_courier_shipment', 'cargo_type_id', 'shipment_type_id')
    def check_is_courier_shipment(self):
        for rec in self:
            if rec.is_courier_shipment:
                if rec.cargo_type_id and not rec.cargo_type_id.is_courier_shipment:
                    raise ValidationError(_("You can't use %s cargo type with courier shipment.") % (rec.cargo_type_id.name))

    def container_override_message_post(self, override_container_number):
        """
        Post message in chatter.
        param override_container_number: dictionary of override containers.
        ex. {record_id (freight.house/master.shipment.package): container_name (string)}
        """
        container_override_type = self.env.context.get('container_override_type')
        msg = ''
        for container in override_container_number:
            package_id = self.package_ids.filtered(lambda pack: pack.id == container) or self.container_ids.filtered(
                lambda cont: cont.id == container)
            field_info = package_id.fields_get(['container_number'])['container_number']
            if container_override_type and container_override_type == 'linked':
                msg += "<p>Container Number override from {} to {} for container: {}</p>".format(
                    'house' if 'house' in self._name else 'master',
                    'master' if 'house' in self._name else 'house', package_id.container_number.name)
            else:
                msg += "<p>Container Number override for container: {}</p>".format(package_id.container_number.name)
            msg += "<ul>"
            msg += """
                    <li>
                        {}: {}
                        <span class="fa fa-long-arrow-right" style='vertical-align: middle;'/>
                        {}
                    </li>""".format(field_info.get('string'),
                                    override_container_number[container], package_id.container_number.name)
            msg += "</ul>"
        if container_override_type and container_override_type == 'linked' and self.env.context.get('control_panel_class') == 'house':
            return msg
        else:
            return msg

    def write(self, vals):
        # override_linked_container: which is linked with house and master shipment
        override_linked_container = {}
        # override_unlinked_container: which is not linked with master shipment
        override_unlinked_container = {}
        package_container = vals.get('package_ids') or vals.get('container_ids')
        if package_container:
            for package_vals in package_container:
                if str(package_vals[1]).isnumeric() and package_vals[2] and package_vals[2].get('container_number'):
                    shipment_package_obj = self.env[self._name + '.package']
                    package_id = shipment_package_obj.browse(package_vals[1]).exists()
                    if package_id and package_id.container_number and package_id.container_number.id != package_vals[2].get('container_number'):
                        parent_id = package_id.master_shipment_pack_id if 'house' in self._name else package_id.house_shipment_pack_id
                        if parent_id:
                            override_linked_container[package_id.id] = package_id.container_number.container_number
                        else:
                            override_unlinked_container[package_id.id] = package_id.container_number.container_number
        res = super().write(vals)

        # post message in chatter for container override
        message = ''
        if override_linked_container:
            if 'house' in self._name:
                message += self.with_context(container_override_type='linked').container_override_message_post(
                    override_linked_container)
                self.parent_id._message_log(body=message, )
            else:
                shipment_package_obj = self.env[self._name + '.package']
                for package_id, container_name in override_linked_container.items():
                    message = ''
                    package_id = shipment_package_obj.browse(package_id).exists()
                    if package_id:
                        message += self.with_context(container_override_type='linked').container_override_message_post(
                            override_linked_container)
                        package_id.house_shipment_id._message_log(body=message, )
        if override_unlinked_container:
            message += self.with_context(container_override_type='unlinked').container_override_message_post(
                override_unlinked_container)
            self._message_log(body=message, )
        return res
