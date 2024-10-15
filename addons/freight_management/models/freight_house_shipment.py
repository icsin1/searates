import base64
import logging
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.tools import format_duration
import json

from lxml import etree

_logger = logging.getLogger(__name__)

HOUSE_STATE = [
    ('created', 'Created'),
    ('booked', 'Booked'),
    ('confirmed', 'Confirmed'),
    ('hawb_generated', 'HAWB Generated'),
    ('hbl_generated', 'HBL Generated'),
    ('nomination_generated', 'Nomination Generated'),
    ('in_transit', 'In Transit'),
    ('arrived', 'Arrived'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

WEIGHT_VOLUME_TRACK_FIELDS = [
    'auto_update_weight_volume',
    'pack_unit',
    'pack_unit_uom_id',
    'gross_weight_unit',
    'gross_weight_unit_uom_id',
    'weight_volume_unit',
    'weight_volume_unit_uom_id',
    'net_weight_unit',
    'net_weight_unit_uom_id',
    'volume_unit',
    'volume_unit_uom_id',
    'chargeable_kg',
]
# FIXME: Once we are ready with stages to make shipment readonly
# READONLY_STAGE = {'created': [('readonly', False)]}
READONLY_STAGE = {}


class FreightHouseShipment(models.Model):
    _name = 'freight.house.shipment'
    _description = 'House Shipment'
    _inherit = ['freight.shipment.mixin', 'freight.customer.mixin', 'freight.shipper.mixin', 'freight.consignee.mixin', 'freight.proxy.shipper.mixin',
                'freight.proxy.consignee.mixin']
    _rec_name = 'display_name'
    _segment_key = 'house_shipments'

    @api.depends('is_courier_shipment', 'mode_type')
    def _compute_shipment_type_domain(self):
        for rec in self:
            domain = []
            if rec.enable_disable_reexport_hs and rec.mode_type in ('sea', 'air'):
                domain.append('|')
                domain.append(('active', '=', True))
                domain.append('&')
                domain.append(('active', '=', False))
                domain.append(('id', '=', self.env.ref('freight_base.shipment_type_reexport').id))
            domain.append('|')
            domain.append(('is_courier_shipment', '=', False))
            domain.append(('is_courier_shipment', '=', rec.is_courier_shipment))
            rec.shipment_type_domain = json.dumps(domain)

    shipment_type_domain = fields.Char(compute='_compute_shipment_type_domain', store=True)

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):

        res = super(FreightHouseShipment, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                                submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form' and not self.env.user.has_group('freight_management.group_super_admin'):
            for node in doc.xpath("//field"):
                if node.get("modifiers") is not None:
                    modifiers = json.loads(node.get("modifiers"))
                    if 'readonly' not in modifiers:
                        modifiers['readonly'] = [['state', 'in', ['cancelled', 'completed']]]
                    else:
                        if not isinstance(modifiers['readonly'], bool):
                            modifiers['readonly'].insert(-1, '|')
                            modifiers['readonly'] += [['state', 'in', ['cancelled', 'completed']]]
                    node.set('modifiers', json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc)
        return res

    display_name = fields.Char(compute='_compute_display_name', store=True)
    name = fields.Char(related='booking_nomination_no', store=True, string='Booking Reference / Nomination Number')
    booking_nomination_no = fields.Char(string='Booking Ref / Nomination No', store=True, copy=False, default='New', readonly=True)
    hbl_number = fields.Char('House BL No', copy=False, states=READONLY_STAGE)
    hbl_number_type = fields.Selection([
        ('nomination_no', 'Nomination No'),
        ('free_hand', 'Free Hand')
    ], string='Import Type', default='nomination_no', required=True, states=READONLY_STAGE)

    inco_term_id = fields.Many2one('account.incoterms', string="Incoterms", states=READONLY_STAGE)
    service_mode_id = fields.Many2one('freight.service.mode', required=True, states=READONLY_STAGE)

    # Customer
    client_id = fields.Many2one('res.partner', states=READONLY_STAGE)
    client_address_id = fields.Many2one('res.partner', states=READONLY_STAGE)

    # Shipper and Consignee
    shipper_id = fields.Many2one('res.partner', string='Shipper/Sending Forwarder', states=READONLY_STAGE)
    shipper_address_id = fields.Many2one('res.partner', string='Shipper Address', states=READONLY_STAGE)
    consignee_id = fields.Many2one('res.partner', string='Consignee/Receiving Forwarder', states=READONLY_STAGE)
    consignee_address_id = fields.Many2one('res.partner', string='Consignee Address', states=READONLY_STAGE)

    # Partners/Parties
    shipment_partner_ids = fields.One2many('freight.house.shipment.partner', 'freight_shipment_id',
                                           string='Parties', states=READONLY_STAGE)
    notify_party_1 = fields.Char(string='Notify Party 1', compute='compute_notify_party_1_destination', store=True)
    destination_agent = fields.Char(string='Destination Agent(FFW)', compute='compute_notify_party_1_destination', store=True)

    # Insurance and Goods Values
    is_insured = fields.Boolean(default=False, states=READONLY_STAGE)
    goods_value_amount = fields.Monetary(string='Goods Value', currency_field='goods_value_currency_id', states=READONLY_STAGE)
    goods_value_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id, states=READONLY_STAGE)
    insurance_value_amount = fields.Monetary(string='Insurance Value', currency_field='insurance_value_currency_id', states=READONLY_STAGE)
    insurance_value_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id, states=READONLY_STAGE)
    policy_number = fields.Char(states=READONLY_STAGE)
    issued_by = fields.Char(states=READONLY_STAGE)
    issued_date = fields.Date(states=READONLY_STAGE)
    policy_holder = fields.Char(states=READONLY_STAGE)

    # Carrier information (copied from Master Shipment)
    voyage_number = fields.Char(string='Voyage No', related="parent_id.voyage_number", store=True, readonly=False, tracking=True)
    vessel_id = fields.Many2one('freight.vessel', string='Vessel', related="parent_id.vessel_id", store=True, readonly=False, tracking=True)
    shipping_line_id = fields.Many2one('freight.carrier', string='Shipping Line', related="parent_id.shipping_line_id", store=True, readonly=False, tracking=True)
    # Commenting below field because it is already available in mixin and has onchange method
    # aircraft_type = fields.Selection(related='parent_id.aircraft_type', store=True)
    enable_disable_shipping_line = fields.Boolean(string="Enable SCAC Code", related='company_id.enable_disable_shipping_line', store=True)
    # Additional Details
    # BOE Details
    boe_number = fields.Char(string='BOE Number', help="Bill of Entry Number", states=READONLY_STAGE)
    boe_date = fields.Date(string='BOE Date', help="Bill of Entry Date", states=READONLY_STAGE)
    ownership = fields.Selection(selection=[('self', 'Self'), ('third_party', 'Third Party')], default='self', states=READONLY_STAGE)
    ownership_id = fields.Many2one('res.partner', string='Ownership Name', domain=[('parent_id', '=', False)], states=READONLY_STAGE)

    # HBL Details
    paid_place_id = fields.Many2one('freight.un.location')
    place_of_issue_id = fields.Many2one('freight.un.location', string='Place of Issue/ Receipt')
    place_of_supply_id = fields.Many2one('freight.un.location', string='Place of Supply/Delivery')
    issue_date = fields.Date(string='Issue Date')
    receipt_date = fields.Date(string='Receipt Date')
    goods_co_id = fields.Many2one('freight.un.location')
    ship_onboard_date = fields.Datetime()
    no_of_origin_docs = fields.Integer(default=1, string='No of Originals')
    no_of_copy_docs = fields.Integer(default=1, string='No of Copies')
    line_number = fields.Integer('Line Number')
    sub_line_number = fields.Integer('SUB Line Number')
    port_cut_off_date = fields.Date('Port Cut-off Date')
    shipper_declared_value = fields.Integer('Shipper Declared Value')
    cargo_received_date = fields.Date('Cargo Received Date')

    # Proxy BL
    is_proxy_bl = fields.Boolean(string='Proxy BL')
    proxy_shipper_id = fields.Many2one('res.partner', string='Proxy Shipper', states=READONLY_STAGE)
    proxy_shipper_address_id = fields.Many2one('res.partner', string='Proxy Shipper Address', states=READONLY_STAGE)
    proxy_consignee_id = fields.Many2one('res.partner', string='Proxy Consignee', states=READONLY_STAGE)
    proxy_consignee_address_id = fields.Many2one('res.partner', string='Proxy Consignee Address', states=READONLY_STAGE)
    shipment_type = fields.Char(related='shipment_type_id.code', string='Shipment Type Code')
    cargo_type = fields.Char(related='cargo_type_id.code', string='Cargo Type Code')
    is_proxy_bl_visible = fields.Boolean(string="Is Proxy BL Visible", default=False)
    remarks = fields.Text("Remarks")
    house_check = fields.Boolean('House Check', compute='_compute_house_check')
    shipper_consignee_check = fields.Boolean('Shipper/Consignee Check', compute='_compute_shipper_consignee_check')
    latest_milestone_id = fields.Many2one('freight.event.type', string="Latest Milestone", compute='_compute_latest_milestone')
    latest_milestone_id = fields.Many2one('freight.event.type', string="Latest Milestone", compute='_compute_latest_milestone', store=True)
    chargeable_volume = fields.Float('Chargeable Volume', store=True, compute='_compute_chargeable_volume')
    chargeable_volume_uom_id = fields.Many2one(
        'uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)], ondelete="restrict")
    calculated_dimension_lwh = fields.Boolean(related='cargo_type_id.calculated_dimension_lwh', store=True)
    shipper_account_numbers = fields.Char(string='Shipper Account Numbers')
    consignee_account_numbers = fields.Char(string='Consignee Account Numbers')

    @api.constrains('shipper_account_numbers', 'consignee_account_numbers')
    def check_shipper_consignee_account_numbers(self):
        for rec in self:
            if rec.shipper_account_numbers and self.search_count([('id', '!=', rec.id), '|', ('shipper_account_numbers', 'ilike', rec.shipper_account_numbers),
                                                                  ('consignee_account_numbers', 'ilike', rec.shipper_account_numbers)]) > 0:
                raise ValidationError(_('Shipper Account Numbers must be unique.'))
            elif rec.consignee_account_numbers and self.search_count([('id', '!=', rec.id), '|', ('consignee_account_numbers', 'ilike', rec.consignee_account_numbers),
                                                                      ('shipper_account_numbers', 'ilike', rec.consignee_account_numbers)]) > 0:
                raise ValidationError(_('Consignee Account Numbers must be unique.'))
            if rec.shipper_account_numbers and rec.consignee_account_numbers:
                if rec.shipper_account_numbers == rec.consignee_account_numbers:
                    raise ValidationError('Shipper Account Numbers and Consignee Account Numbers must be unique.')

    @api.depends('package_ids', 'commodity_ids')
    def _compute_chargeable_volume(self):
        for ship in self:
            ship.chargeable_volume = sum(ship.package_ids.commodity_ids.mapped('chargeable_volume'))
            ship.chargeable_volume_uom_id = ship.package_ids.commodity_ids.mapped('chargeable_volume_uom_id')

    @api.depends('company_id')
    def _compute_house_check(self):
        is_house_check = self.env['ir.config_parameter'].sudo().get_param('freight_management.enable_non_mandatory_fields')
        for rec in self:
            if is_house_check:
                rec.house_check = True
            else:
                rec.house_check = False

    @api.depends('company_id')
    def _compute_shipper_consignee_check(self):
        shipper_consignee_check = self.env['ir.config_parameter'].sudo().get_param(
            'freight_management.shipper_consignee_non_mandatory')
        for rec in self:
            if shipper_consignee_check:
                rec.shipper_consignee_check = True
            else:
                rec.shipper_consignee_check = False

    @api.depends('event_ids')
    def _compute_latest_milestone(self):
        for record in self:
            for milestone in record.event_ids:
                record.latest_milestone_id = milestone.event_type_id.id

    @api.onchange('shipping_line_id', 'enable_disable_shipping_line', 'transport_mode_id')
    def _onchange_shipping_line(self):
        if self.transport_mode_id.mode_type == 'sea' and self.enable_disable_shipping_line:
            if self.shipping_line_id:
                self.carrier_booking_reference_number = self.shipping_line_id.scac_code
            else:
                self.carrier_booking_reference_number = False
        else:
            self.carrier_booking_reference_number = False

    @api.model
    def _shipment_pre_auto_reminder(self):
        two_days_before_start = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d 00:00:00')
        two_days_before_end = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d 23:59:59')
        house_shipment_ids = self.env['freight.house.shipment'].sudo().search([
            ('eta_time', '>=', two_days_before_start),
            ('eta_time', '<', two_days_before_end),
            ('export_state', 'not in', ['completed', 'cancelled'])])
        house_shipment_ids += self.env['freight.house.shipment'].sudo().search([
            ('etd_time', '>=', two_days_before_start),
            ('etd_time', '<', two_days_before_end),
            ('export_state', 'not in', ['completed', 'cancelled']),
            ('transport_mode_id', '=', self.env.ref('freight_base.transport_mode_land').id)])
        for shipment in house_shipment_ids:
            template_id = self.env.ref("freight_management.shipment_pre_alert_notify", raise_if_not_found=False)
            if template_id:
                try:
                    template_id.sudo().send_mail(shipment.id, force_send=True, raise_exception=True)
                    logging.info("Mail Sent Successfully")
                except MailDeliveryException:
                    logging.error("Mail Sending Failed")

    @api.depends('shipment_partner_ids')
    def compute_notify_party_1_destination(self):
        notify_party_1_names = []
        destination_agent_names = []
        for party in self.shipment_partner_ids:
            if self.env.ref('freight_base.org_type_notify_1').id == party.partner_type_id.id:
                notify_party_1_names.append(party.partner_id.display_name)
            if self.env.ref('freight_base.org_type_destination_agent').id == party.partner_type_id.id:
                destination_agent_names.append(party.partner_id.display_name)
        if len(notify_party_1_names) > 1:
            notify_party_1_names = ", ".join(notify_party_1_names)
        else:
            notify_party_1_names = notify_party_1_names and notify_party_1_names[0] or ''
        self.notify_party_1 = notify_party_1_names

        if len(destination_agent_names) > 1:
            destination_agent_names = ", ".join(destination_agent_names)
        else:
            destination_agent_names = destination_agent_names and destination_agent_names[0] or ''
        self.destination_agent = destination_agent_names

    # added unlink so when deleting reexport
    def unlink(self):
        for hs in self:
            if hs.shipment_type_key == 're_export':
                import_record = self.search([('hbl_number', '=', hs.hbl_number), ('shipment_type_key', '=', 'import')])
                if import_record:
                    import_record.is_reexported = False
        return super(FreightHouseShipment, self).unlink()

    @api.onchange('mode_type', 'shipment_type_id', 'cargo_type')
    def onchange_mode_shipment_cargo_type(self):
        for rec in self:
            if (rec.mode_type == 'sea') and (rec.shipment_type == 'EXP') and (rec.cargo_type in ['FCL', 'LCL']):
                rec.is_proxy_bl_visible = True
            else:
                rec.is_proxy_bl_visible = False

    # HAZ Details
    is_hazardous = fields.Boolean(string='Is HAZ')
    haz_class_id = fields.Many2one('haz.sub.class.code', string='HAZ Class')
    haz_un_number = fields.Char(string='UN #')
    haz_remark = fields.Text('HAZ Remark')

    # STUFFING / DESTUFFING / INSTRUCTIONS  Details

    contact_number = fields.Char(string='Contact Details')
    location = fields.Char(string='Location')
    instructions = fields.Text(string='Instructions')

    # customs detail
    has_customs = fields.Boolean(default=False, string="Is Custom Required?")
    customs_ad_code = fields.Char(string='AD Code')
    customs_location_id = fields.Many2one('freight.custom.location', string='Custom Location')
    customs_document_ids = fields.One2many('freight.house.shipment.customs.document', 'shipment_id', string='Custom Documents')
    customs_declaration_number = fields.Char(string='Declaration Number')
    customs_declaration_date = fields.Date('Declaration Date')
    customs_clearance_datetime = fields.Datetime('Custom Clearance Date & Time')
    tariff_determination_number = fields.Char('Tariff Determination Number(TDN)')
    value_determination_number = fields.Char('Value Determination Number(VDN)')
    customs_procedure_code = fields.Char('Customs Procedure Code')
    igm_number = fields.Char('IGM Number')
    igm_date = fields.Date('IGM Date')
    do_number = fields.Char('DO Number')
    do_date = fields.Date('DO Date')

    # Master: Ext. carrier Booking details (copied from master shipment)
    carrier_booking_reference_number = fields.Char(string='MBL', related="parent_id.carrier_booking_reference_number", store=True, readonly=False)
    carrier_booking_carrier_number = fields.Char(string='Carrier Number', related='parent_id.carrier_booking_carrier_number', store=True, readonly=False)
    carrier_agent_id = fields.Many2one('res.partner', string='Carrier Agent',
                                       related='parent_id.carrier_agent_id', store=True, readonly=False)
    carrier_forwarder_reference_number = fields.Char('Forwarder Reference Number',
                                                     related='parent_id.carrier_forwarder_reference_number', store=True, readonly=False)
    carrier_vessel_cut_off_datetime = fields.Datetime(string='Vessel Cut-Off Datetime',
                                                      related='parent_id.carrier_vessel_cut_off_datetime', store=True, readonly=False)
    carrier_vgm_cut_off_datetime = fields.Datetime(
        'VGM Cut-Off Datetime', help="Verified Gross Mass Cut-Off Datetime",
        related='parent_id.carrier_vgm_cut_off_datetime', store=True, readonly=False)
    carrier_warehouse_cut_off_datetime = fields.Datetime('Warehouse Cut-Off Datetime',
                                                         related='parent_id.carrier_warehouse_cut_off_datetime', store=True, readonly=False)
    ams_number = fields.Text('AMS Number', related="parent_id.ams_number", readonly=False)

    # Packages
    # If LCL
    package_ids = fields.One2many('freight.house.shipment.package', 'shipment_id', string='Packages',
                                  domain=[('package_mode', '=', 'package'), ('container_package_id', '=', False)])
    # If FCL
    is_part_bl = fields.Boolean('Is Part BL', compute='_compute_is_part_bl', readonly=False, store=True)
    no_of_part_bl = fields.Selection([('1', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5)], string='No of Part BL')
    part_bl_ids = fields.One2many('freight.house.shipment.part.bl', 'shipment_id', string='Part BL')
    container_ids = fields.One2many('freight.house.shipment.package', 'shipment_id', string='Containers',
                                    domain=[('package_mode', '=', 'container'), ('container_package_id', '=', False)])
    container_number_list_file = fields.Binary()
    container_document_file_name = fields.Char()
    upload_file_message = fields.Text(copy=False)
    packages_count = fields.Integer(compute='_compute_packages_count', store=True)
    containers_count = fields.Integer(compute='_compute_packages_count', store=True)
    list_containers_count = fields.Integer(compute='_compute_list_container_count')
    commodity_ids = fields.One2many('freight.house.package.commodity', 'shipment_id', string='Package Commodity')

    # routes
    route_ids = fields.One2many('freight.house.shipment.route', 'shipment_id', string='Routes')

    # Events
    event_ids = fields.One2many('freight.house.shipment.event', 'shipment_id', string='Milestones Tracking')

    # Documents
    document_ids = fields.One2many('freight.house.shipment.document', 'shipment_id', string='Documents')
    document_count = fields.Integer(compute='_compute_document_count')

    # Shipment State
    state = fields.Selection(HOUSE_STATE, default='created', tracking=True, group_expand='_expand_states')
    import_state = fields.Selection(related='state', string='Import State')
    export_state = fields.Selection(related='state', string='Export State')
    reexport_state = fields.Selection(related='state', string='ReExport State')
    air_export_state = fields.Selection(related='state', string='Air-Freight Export State')
    cross_state = fields.Selection(related='state', string='Cross State')
    domestic_export_state = fields.Selection(related='state', string='Domestic Export State')

    # Terms and Conditions
    terms_ids = fields.One2many('freight.house.shipment.terms', 'shipment_id', string='Terms & Conditions')

    tag_ids = fields.Many2many('freight.shipment.tag', 'freight_house_shipment_tag_rel', 'shipment_id', 'tag_id', copy=False, string='Tags', states=READONLY_STAGE)

    entry_detail = fields.Selection(
        selection=[('ata', 'ATA (ATA Carnet Number)'), ('pmt', 'PMT (Customs Permit/Clearance Number)'), ('tsn', 'TSN (Transhipment Number)')])
    entry_detail_number = fields.Char()
    release_type = fields.Selection(
        selection=[
            ('brr', 'BRR (Letter to credit bank release)'), ('bsd', 'BSD (Sight Draft Bank release)'), ('btd', 'BTD (Time Draft Bank release)'), ('cad', 'CAD (Cash Against Documentation)'),
            ('csh', 'CSH (Company/Cashier Check)'), ('ebl', 'EBL (Express Bill of Loading)'), ('loi', 'LOI (Letter of Indemnity)'), ('non', 'NON (Not Negotiable Unless Consigned to order)'),
            ('obl', 'OBL (Original Bill Of Lading)'), ('obo', 'OBO (Original Bill- Surrendered at  origin)'), ('obr', 'OBR (Original Bill- required at  Destination)'),
            ('swb', 'SWB (Seaway Bill)')])
    payment_terms = fields.Selection(selection=[('ppx', 'Prepaid (PPX)'), ('ccx', 'Collect (CCX)')])
    free_day = fields.Char()
    container_number = fields.Char(compute='cal_container_number', store=True)
    container_type = fields.Char(compute='cal_container_type', store=True)

    # Readonly Abstract model column for house shipment
    company_id = fields.Many2one(states=READONLY_STAGE)
    enable_disable_part_bl = fields.Boolean(related='company_id.enable_disable_part_bl', store=True)
    shipment_date = fields.Date(states=READONLY_STAGE, default=lambda self: fields.Date.today())
    origin_un_location_id = fields.Many2one(states=READONLY_STAGE)
    destination_un_location_id = fields.Many2one(states=READONLY_STAGE)
    origin_port_un_location_id = fields.Many2one(states=READONLY_STAGE, string='Origin Port/Airport')
    destination_port_un_location_id = fields.Many2one(states=READONLY_STAGE, string='Destination Port/Airport')

    lcl_package_data_file = fields.Binary()
    lcl_package_data_file_name = fields.Char()

    # Vessel Certificate Document
    lc_number = fields.Char(string='L/C Number', copy=False)
    lc_number_updated_on = fields.Datetime(string='L/C number Updated On', copy=False, store=True,
                                           compute="_compute_updated_on_datetime")
    commercial_invoice = fields.Char(string='Commercial Invoice', copy=False)
    commercial_invoice_updated_on = fields.Datetime(string='Commercial Invoice Updated On', copy=False, store=True,
                                                    compute="_compute_updated_on_datetime")
    customer_ref_no = fields.Char(string='Customer Ref. No.')
    customer_remarks = fields.Text(string='Customer Remarks')
    marks_and_no = fields.Text(string='Marks & No')

    is_reexported = fields.Boolean(string='Is ReExported', default=False, copy=False)
    enable_disable_reexport_hs = fields.Boolean(string="Enable ReExport Shipment",
                                                related='company_id.enable_disable_reexport_hs', store=True)
    import_job_count = fields.Integer(compute='_compute_import_job_count')
    reexport_job_count = fields.Integer(compute='_compute_reexport_job_count')
    shipment_note = fields.Text(string='Shipment Note')
    rate_class = fields.Selection([
        ('m', 'M'),
        ('n', 'N'),
        ('q', 'Q'),
        ('s', 'S'),
        ('c', 'C')
    ], string="Rate Class")

    # Cut - Off Dates
    enable_cut_off_dates = fields.Boolean(related="company_id.enable_cut_off_dates")
    order_no = fields.Char("Order no")
    paperless_code = fields.Char("Paperless code")
    cy_date = fields.Date("CY Date")
    return_date = fields.Date("Return Date")
    cy_yard = fields.Text("CY Yard")
    return_yard = fields.Text("Return Yard")
    closing_date = fields.Date("Closing Date")
    closing_time = fields.Float("Closing Time")
    port_regulations = fields.Text("PORT Regulations")
    remark = fields.Text("Remark")
    booking = fields.Char("Booking", related="carrier_booking_carrier_number", store=True)
    enable_feeder_details = fields.Boolean(related="company_id.enable_feeder_details")

    feeder_voyage_number = fields.Char(string='Feeder Voyage No', tracking=True)
    feeder_vessel_id = fields.Many2one('freight.vessel', string='Feeder Vessel', tracking=True)
    feeder_shipping_line_id = fields.Many2one('freight.carrier', string='Feeder Shipping Line', tracking=True)
    shipment_for = fields.Selection([('shipment', 'Shipment'), ('job', 'Service Job')], default='shipment', string='House Shipment For')
    # Address Fields
    pickup_address = fields.Text('Pickup Address')
    delivery_address = fields.Text('Delivery Address')
    incoterm_check = fields.Boolean(related='inco_term_id.incoterm_check')
    customs_be_type_id = fields.Many2one('custom.master.be.type', string='BE Type')

    # Enable edit of External Carrier Bookings
    allow_edit_external_carrier_bookings = fields.Boolean(compute="_compute_external_carrier_bookings")

    @api.depends('transport_mode_id', 'cargo_type_id')
    def _compute_external_carrier_bookings(self):
        transport_mode_id = self.env.ref('freight_base.transport_mode_sea').id
        cargo_type_id = self.env.ref('freight_base.cargo_type_sea_fcl').id
        for rec in self:
            if rec.company_id.allow_edit_external_carrier_bookings and rec.transport_mode_id.id == transport_mode_id and rec.cargo_type_id.id == cargo_type_id:
                rec.allow_edit_external_carrier_bookings = True
            else:
                rec.allow_edit_external_carrier_bookings = False

    _sql_constraints = [
        ('name_unique', 'unique(booking_nomination_no)', 'The Booking Ref / Nomination Number must be unique per Shipment!'),
        ('hbl_number_unique', 'CHECK(1=1)', "IGNORE")
    ]

    @api.onchange('closing_time')
    def _onchange_closing_time(self):
        try:
            time_str = format_duration(self.closing_time)
            datetime.strptime(time_str, '%H:%M')
        except Exception:
            self.closing_time = False
            return {
                'warning': {
                    'message': _('Invalid Closing Time!')
                }
            }

    @api.depends('hbl_number')
    def _compute_import_job_count(self):
        for hs in self:
            if hs.hbl_number:
                hs.import_job_count = self.search_count([('hbl_number', '=', hs.hbl_number), ('shipment_type_key', '=', 'import')])
            else:
                hs.import_job_count = 0

    @api.depends('hbl_number')
    def _compute_reexport_job_count(self):
        for hs in self:
            if hs.hbl_number:
                hs.reexport_job_count = self.search_count([('hbl_number', '=', hs.hbl_number), ('shipment_type_key', '=', 're_export')])
            else:
                hs.reexport_job_count = 0

    @api.depends('packaging_mode', 'shipment_type_key', 'mode_type')
    def _compute_is_part_bl(self):
        for rec in self:
            rec.is_part_bl = False
            if rec.packaging_mode != 'container' or rec.shipment_type_key != 'export' or rec.mode_type != 'sea':
                rec.is_part_bl = False

    @api.constrains('part_bl_ids', 'no_of_part_bl')
    def check_part_bl_lines(self):
        for rec in self:
            if len(rec.part_bl_ids) > int(rec.no_of_part_bl):
                raise ValidationError('Can not add more than %s line(s) for Part BL' % rec.no_of_part_bl)

    @api.depends('hbl_number', 'booking_nomination_no')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.hbl_number or rec.booking_nomination_no

    @api.constrains('shipment_partner_ids')
    def _check_shipment_partner_ids(self):
        for shipment in self:
            existing_vendor_parties = []
            for party in shipment.shipment_partner_ids.filtered(lambda p: p.partner_type_id.is_vendor):
                if (party.partner_type_id.id, party.partner_id.id,) in existing_vendor_parties:
                    raise UserError(_('Duplication of party type and party cannot be Allowed..'))
                existing_vendor_parties.append((party.partner_type_id.id, party.partner_id.id,))
            existing_other_parties = []
            for party in shipment.shipment_partner_ids.filtered(lambda p: not p.partner_type_id.is_vendor):
                if party.partner_type_id.id in existing_other_parties:
                    raise UserError(_('Duplication of non vendor party type cannot be Allowed.'))
                existing_other_parties.append(party.partner_type_id.id)

    def _expand_states(self, states, domain, order):
        return [key for key, dummy in type(self).state.selection]

    @api.depends('container_ids', 'package_ids', 'package_ids.quantity')
    def _compute_packages_count(self):
        for rec in self:
            rec.packages_count = sum(rec.package_ids.mapped('quantity')) if rec.packaging_mode == 'package' else 0
            rec.containers_count = sum(rec.container_ids.mapped('quantity')) if rec.packaging_mode == 'container' else 0

    def _compute_list_container_count(self):
        for rec in self:
            rec.list_containers_count = 0
            if rec.packaging_mode == 'container':
                rec.list_containers_count = len(rec.container_ids.filtered(lambda container: container and container.container_number))
            if rec.packaging_mode == 'package':
                rec.list_containers_count = len(rec.package_ids.filtered(lambda container: container and container.container_number))

    @api.constrains('hbl_number', 'state')
    def _check_unique_hbl_number(self):
        for house in self:
            name = 'HBL'
            if house.mode_type == 'air':
                name = 'HAWB'
            elif house.mode_type == 'land':
                name = 'HLR'
            if house.hbl_number:
                domain = [('hbl_number', '=ilike', house.hbl_number), ('company_id', '=', house.company_id.id), ('shipment_type_key', '=', 're_export')]
                if self.search_count(domain) > 1:
                    raise ValidationError(_('%s Number must be unique!') % (name))
            elif not house.company_id.shipment_status_change or not house.is_direct_shipment:
                if house.state not in ['created', 'cancelled']:
                    raise ValidationError(_('%s Number is required.') % (name))

    @api.onchange('client_id')
    def _onchange_client_id(self):
        for rec in self:
            if rec.client_id and rec._context.get('force_change'):
                rec.ownership_id = rec.client_id.id
            rec.sales_agent_id = rec.client_id.user_id.id or self.env.user.id
        if self._context.get('force_change'):
            return super()._onchange_client_id()

    @api.onchange('consignee_id')
    def _onchange_consignee_id(self):
        if self._context.get('force_change'):
            return super()._onchange_consignee_id()

    @api.onchange('shipper_id')
    def _onchange_shipper_id(self):
        if self._context.get('force_change'):
            return super()._onchange_shipper_id()

    @api.depends(
        'auto_update_weight_volume',
        'cargo_is_package_group',
        'container_ids',
        'container_ids.weight_unit',
        'container_ids.weight_unit_uom_id',
        'container_ids.volume_unit',
        'container_ids.volume_unit_uom_id',
        'container_ids.volumetric_weight',
        'package_ids',
        'package_ids.pack_count',
        'package_ids.weight_unit',
        'package_ids.weight_unit_uom_id',
        'package_ids.volume_unit',
        'package_ids.volume_unit_uom_id',
        'package_ids.volumetric_weight',
        'package_ids.total_weight_unit',
        'package_ids.total_volume_unit',
        'package_ids.total_volumetric_weight'
    )
    def _compute_auto_weight_volume(self):
        volume_uom = self.env.company.volume_uom_id
        weight_uom = self.env.company.weight_uom_id
        package_uom = self.env.ref('freight_base.pack_uom_pkg')

        for shipment in self:
            # Keep Manual value when No auto update
            if not shipment.auto_update_weight_volume:
                shipment.gross_weight_unit = shipment.gross_weight_unit
                shipment.weight_volume_unit = shipment.weight_volume_unit
                shipment.gross_weight_unit_uom_id = shipment.gross_weight_unit_uom_id
                shipment.weight_volume_unit_uom_id = shipment.weight_volume_unit_uom_id
                shipment.pack_unit = shipment.pack_unit
                shipment.pack_unit_uom_id = shipment.pack_unit_uom_id
                continue
            # Auto update
            if shipment.cargo_is_package_group:
                total_gross_weight = sum([p.container_weight_unit_uom_id._compute_quantity(p.total_weight_unit, weight_uom, round=False) for p in shipment.package_ids])
                total_volumetric_weight_unit = sum([p.container_volumetric_weight_unit_uom_id._compute_quantity(p.total_volumetric_weight, weight_uom, round=False) for p in shipment.package_ids])
                total_volume_unit = sum([p.container_volume_unit_uom_id._compute_quantity(p.total_volume_unit, volume_uom, round=False) for p in shipment.package_ids])
                total_net_weight_unit = sum([p.container_net_weight_unit_uom_id._compute_quantity(p.total_net_weight, weight_uom, round=False) for p in shipment.package_ids])
                pack_unit = sum(shipment.package_ids.mapped('quantity'))
                package_uom = shipment.package_ids.mapped('package_type_id') if len(shipment.package_ids.mapped('package_type_id')) == 1 else package_uom
            else:
                total_gross_weight = sum([c.container_weight_unit_uom_id._compute_quantity(c.total_weight_unit, weight_uom, round=False) for c in shipment.container_ids])
                total_volumetric_weight_unit = sum([c.container_volumetric_weight_unit_uom_id._compute_quantity(c.total_volumetric_weight, weight_uom, round=False) for c in shipment.container_ids])
                total_volume_unit = sum([p.container_volume_unit_uom_id._compute_quantity(p.total_volume_unit, volume_uom, round=False) for p in shipment.container_ids])
                total_net_weight_unit = sum([c.container_net_weight_unit_uom_id._compute_quantity(c.total_net_weight, weight_uom, round=False) for c in shipment.container_ids])
                pack_unit = sum(shipment.container_ids.mapped('pack_count'))
                package_uom_list = []
                for line in shipment.container_ids:
                    for package in line.package_group_ids:
                        package_uom_list.append(package.package_type_id)
                package_uom = package_uom_list[0] if len(set(package_uom_list)) == 1 else package_uom

            shipment.gross_weight_unit, shipment.gross_weight_unit_uom_id = (round(total_gross_weight or shipment.gross_weight_unit, 3),
                                                                             (weight_uom.id or shipment.gross_weight_unit_uom_id and shipment.gross_weight_unit_uom_id.id))
            shipment.weight_volume_unit, shipment.weight_volume_unit_uom_id = (round(total_volumetric_weight_unit or shipment.weight_volume_unit, 3),
                                                                               (weight_uom.id or shipment.weight_volume_unit_uom_id and shipment.weight_volume_unit_uom_id.id))
            shipment.net_weight_unit, shipment.net_weight_unit_uom_id = (round(total_net_weight_unit or shipment.net_weight_unit, 3),
                                                                         (weight_uom.id or shipment.net_weight_unit_uom_id and shipment.net_weight_unit_uom_id.id))
            shipment.volume_unit, shipment.volume_unit_uom_id = (round(total_volume_unit or shipment.volume_unit, 3),
                                                                 (volume_uom.id or shipment.volume_unit_uom_id and shipment.volume_unit_uom_id.id))
            shipment.pack_unit, shipment.pack_unit_uom_id = (round(pack_unit or shipment.pack_unit, 3),
                                                             (package_uom.id or shipment.pack_unit_uom_id and shipment.pack_unit_uom_id.id))

    def _convert_weight_unit(self, weight_uom):
        self.ensure_one()
        return round(self.chargeable_uom_id._compute_quantity(self.chargeable_kg, weight_uom), 3)

    def get_weight_uom_in_invoice_report(self):
        return self.chargeable_uom_id or self.company_id.weight_uom_id or self.env.ref('uom.product_uom_kgm')

    def get_volume_uom_in_invoice_report(self):
        return self.company_id.volume_uom_id or self.env.ref('uom.product_uom_cubic_meter')

    def _convert_volume_unit(self, volume_uom):
        self.ensure_one()
        return round(self.volume_unit_uom_id._compute_quantity(self.volume_unit, volume_uom), 3)

    def _get_partner_field_list(self, values):
        self.ensure_one()
        return list(filter(
            lambda field: field in values and self._fields[field].comodel_name == 'res.partner', self._fields.keys()
        ))

    def _update_parties(self, vals):
        self.ensure_one()
        # Required sudo() as field level access is not granted to all users
        self = self.sudo()
        shipment_partners = []
        partner_type_ids = []
        for partner_field in self._get_partner_field_list(vals):
            partner_id = self[partner_field]
            partner_type_field = self.env['res.partner.type.field'].sudo().search([('model_id.model', '=', self._name), ('field_id.name', '=', partner_field)], order="id desc", limit=1)
            if partner_type_field and (partner_type_field.type_id.id not in partner_type_ids):
                partner_type_ids.append(partner_type_field.type_id.id)
                shipment_partner_exist = self.shipment_partner_ids.filtered(lambda party: party.partner_type_id.id == partner_type_field.type_id.id)
                if partner_field == 'client_id':
                    address_id = self.client_address_id
                elif partner_field == 'shipper_id':
                    address_id = self.shipper_address_id
                elif partner_field == 'consignee_id':
                    address_id = self.consignee_address_id
                elif partner_field == 'client_address_id':
                    address_id = self.client_address_id
                    partner_id = self.client_id
                elif partner_field == 'shipper_address_id':
                    address_id = self.shipper_address_id
                    partner_id = self.shipper_id
                elif partner_field == 'consignee_address_id':
                    address_id = self.consignee_address_id
                    partner_id = self.consignee_id
                elif partner_field == 'notify_party_1':
                    address_id = shipment_partner_exist.party_address_id
                    partner_id = shipment_partner_exist.partner_id
                elif partner_field == 'destination_agent':
                    address_id = shipment_partner_exist.party_address_id
                    partner_id = shipment_partner_exist.partner_id
                if shipment_partner_exist:
                    shipment_partners.append((3, shipment_partner_exist.id) if not partner_id else (1, shipment_partner_exist.id, {
                        'partner_id': partner_id.id,
                        'party_address_id': address_id.id,
                    }))
                elif partner_id:
                    shipment_partners.append((0, 0, {
                        'partner_id': partner_id.id,
                        'partner_type_id': partner_type_field.type_id.id,
                        'party_address_id': address_id.id,
                    }))

        if shipment_partners:
            self.write({'shipment_partner_ids': shipment_partners})
        self.sync_party_address()

    def sync_party_address(self):
        for line in self.shipment_partner_ids:
            if line.partner_type_id == self.env.ref('freight_base.org_type_customer'):
                line.party_address_id = self.client_address_id.id
            if line.partner_type_id == self.env.ref('freight_base.org_type_shipper'):
                line.party_address_id = self.shipper_address_id.id
            if line.partner_type_id == self.env.ref('freight_base.org_type_consignee'):
                line.party_address_id = self.consignee_address_id.id

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if not self.shipment_type_id or not self.cargo_type_id or not self.transport_mode_id:
            raise UserError(_("User Could Not Duplicate The House Shipment with out Transport Mode, Shipment Type and Cargo Type ."))
        record = super().copy(default)
        if record.shipment_type_id:
            record.shipment_type_id = False
        if record.cargo_type_id:
            record.cargo_type_id = False
        if record.transport_mode_id:
            record.transport_mode_id = False
        return record

    @api.model_create_single
    def create(self, values):
        rec = super().create(values)
        rec._update_parties(values)
        rec._update_documents_list()
        return rec

    def _prepare_weight_volume_tracking_msg(self, tracking_fields):
        self.ensure_one()
        track_fields = tracking_fields[self.id]
        msg = "<p>Declared Weight & Volume</p>"
        msg += "<ul>"
        for field_name, value in track_fields.items():
            field_info = self.fields_get([field_name])[field_name]
            old_value = value
            new_value = self[field_name]
            if field_info.get('type') == "many2one":
                old_value = old_value.display_name
                new_value = new_value.display_name
            msg += """
                <li>
                    {}: {}
                    <span class="fa fa-long-arrow-right" style='vertical-align: middle;'/>
                    {}
                </li>""".format(field_info.get('string'), old_value, new_value)
        msg += "</ul>"
        return msg

    def _get_weight_volume_tracking(self, vals={}):
        self.ensure_one()
        tracking_fields_values = {}
        # if any of the vals keys is in tracking fields list
        updated_fields = set(vals.keys()).intersection(set(WEIGHT_VOLUME_TRACK_FIELDS))
        value_changed = False
        for updated_field in updated_fields:
            field_info = self.fields_get([updated_field])[updated_field]
            if field_info.get('type') == "many2one" and vals.get(updated_field) != self[updated_field].id:
                value_changed = True
            elif field_info.get('type') != "many2one" and vals.get(updated_field) != self[updated_field]:
                value_changed = True
        if updated_fields and value_changed:
            for key in WEIGHT_VOLUME_TRACK_FIELDS:
                tracking_fields_values.update({
                    key: self[key]
                })
        return tracking_fields_values

    def house_container_tracking_fields(self, vals):
        self.ensure_one()
        tracking_fields_values = {}
        for container_ids_vals in vals.get('container_ids'):
            if container_ids_vals[0] == 1 and 'container_number' in container_ids_vals[2]:
                container_record = self.container_ids.browse(container_ids_vals[1])
                container_number_id = self.env['freight.master.shipment.container.number'].browse(container_ids_vals[2].get('container_number'))
                if container_record.container_number and not container_record.container_number.shipment_id and container_number_id.shipment_id:
                    tracking_fields_values[container_record.id] = container_record.container_number.container_number
        return tracking_fields_values

    def write(self, vals):
        tracking_fields = {}
        # context = self.env.context
        # Finding Declared Weight Volume fields change snap
        if 'auto_update_weight_volume' in vals:
            for shipment in self:
                tracking_fields[shipment.id] = shipment._get_weight_volume_tracking(vals)

        res = super().write(vals)

        # Update Parties only if Party related field changed
        keys_list = ['shipment_partner_ids', 'client_id', 'client_address_id', 'shipper_id', 'shipper_address_id', 'consignee_id', 'consignee_address_id']
        if set(keys_list).intersection(vals.keys()):
            for shipment in self:
                if not self._context.get('updated_from_line'):
                    shipment._update_parties(vals)

        for shipment in self:
            # Logging declared weight volume fields change log
            if tracking_fields.get(shipment.id):
                msg = shipment._prepare_weight_volume_tracking_msg(tracking_fields)
                shipment._message_log(body=msg,)
        return res

    def _update_documents_list(self):
        self.ensure_one()
        document_types = self.env['freight.document.type'].sudo().search([('model_id.model', '=', self._name)])
        documents = [(0, 0, {
            'name': doc_type.name,
            'document_type_id': doc_type.id,
            'datetime': self.create_date
        }) for doc_type in document_types]
        self.write({'document_ids': documents})

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    def action_shipment_documents(self):
        self.ensure_one()
        return {
            'name': _('Shipment Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.house.shipment.document',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('shipment_id', 'in', self.ids)],
            'context': {'default_shipment_id': self.id, 'search_default_group_by_mode': 1},
            'target': 'current',
        }

    def action_remove_all_packages(self):
        self.ensure_one()
        self.package_ids.unlink()
        self.container_ids.unlink()
        self.upload_file_message = False

    def action_open_shipment_master(self):
        self.ensure_one()
        return {
            'name': 'Master Shipment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.master.shipment',
            'context': {
                'control_panel_class': 'master',
                'show_master_shipment': True,
            },
            'domain': [('id', '=', self.parent_id.id)],
            'res_id': self.parent_id.id,
        }

    def action_change_status(self):
        self.ensure_one()
        default_context = {
            'default_shipment_id': self.id
        }
        if (self.mode_type == 'sea' and self.shipment_type_key == 'export') or self.shipment_type_key == 'import' or self.shipment_type_key == 're_export':
            default_context.update({'default_{}_state'.format(self.shipment_type_key): self.state})
        if self.mode_type == 'air' and self.shipment_type_key == 'export':
            default_context.update({'default_air_{}_state'.format(self.shipment_type_key): self.state})
        if self.mode_type == 'land' and self.shipment_type_key == 'export':
            default_context.update({'default_road_{}_state'.format(self.shipment_type_key): self.state})

        return {
            'name': 'Change Status',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.house.shipment.status',
            'context': default_context
        }

    def action_gen_reexport_shipment(self):
        self.ensure_one()
        reexport_shipment = self.copy({'shipment_type_id': self.env.ref('freight_base.shipment_type_reexport').id, 'hbl_number': self.hbl_number})
        self.is_reexported = True
        return {
            'name': 'ReExported Shipment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.house.shipment',
            'context': {'create': False},
            'domain': [('id', '=', reexport_shipment.id)],
            'res_id': reexport_shipment.id,
        }

    def action_open_re_export_job(self):
        self.ensure_one()
        if self.hbl_number:
            return {
                'name': 'ReExported House Shipment',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'freight.house.shipment',
                'context': {'create': False},
                'domain': [('hbl_number', '=', self.hbl_number), ('shipment_type_id', '=', self.env.ref('freight_base.shipment_type_reexport').id)],

            }
        else:
            pass

    def action_open_import_job(self):
        self.ensure_one()
        if self.hbl_number:
            return {
                'name': 'Import House Shipment',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'freight.house.shipment',
                'context': {'create': False},
                'domain': [('hbl_number', '=', self.hbl_number), ('shipment_type_id', '=', self.env.ref('freight_base.shipment_type_import').id)],

            }
        else:
            pass

    def action_create_master_shipment(self):
        self.ensure_one()
        if self.parent_id:
            raise UserError(_("Master Shipment already attached."))
        default_shipment_vals = {
            'default_company_id': self.company_id.id,
            'default_shipment_date': self.shipment_date,
            'default_transport_mode_id': self.transport_mode_id.id,
            'default_cargo_type_id': self.cargo_type_id.id,
            'default_shipment_type_id': self.shipment_type_id.id,
            'default_service_mode_id': self.service_mode_id.id,
            'default_pack_unit': self.pack_unit,
            'default_pack_unit_uom_id': self.pack_unit_uom_id.id,
            'default_gross_weight_unit': self.gross_weight_unit,
            'default_gross_weight_unit_uom_id': self.gross_weight_unit_uom_id.id,
            'default_volume_unit': self.volume_unit,
            'default_volume_unit_uom_id': self.volume_unit_uom_id.id,
            'default_net_weight_unit': self.net_weight_unit,
            'default_net_weight_unit_uom_id': self.net_weight_unit_uom_id.id,
            'default_weight_volume_unit': self.weight_volume_unit,
            'default_weight_volume_unit_uom_id': self.weight_volume_unit_uom_id.id,
            'default_house_shipment_ids': [(4, self.id)],
            'default_is_direct_shipment': self.is_direct_shipment,
            'default_origin_un_location_id': self.origin_un_location_id.id,
            'default_origin_port_un_location_id': self.origin_port_un_location_id.id,
            'default_etd_time': self.etd_time,
            'default_destination_un_location_id': self.destination_un_location_id.id,
            'default_destination_port_un_location_id': self.destination_port_un_location_id.id,
            'default_eta_time': self.eta_time,
            'default_atd_time': self.atd_time,
            'default_ata_time': self.ata_time,
            'default_aircraft_type': self.aircraft_type,
            'default_handling_info': self.handling_info,
            'default_commodity': self.commodity,
            'default_declared_value_carrier': self.declared_value_carrier,
            'default_declared_value_customer': self.declared_value_customer,
            'default_accounting_info': self.accounting_info,
            'default_iata_rate': self.iata_rate,
            'default_tag_ids': [(6, 0, self.tag_ids.ids)],
            'default_is_courier_shipment': self.is_courier_shipment,
            'default_event_ids': [
                (0, 0, {
                    'event_type_id': line.event_type_id.id,
                    'location': line.location,
                    'description': line.description,
                    'estimated_datetime': line.estimated_datetime,
                    'actual_datetime': line.actual_datetime,
                    'public_visible': line.public_visible,
                    'house_shipment_event_id': line.id,
                    'shipment_id': self.id}) for line in self.event_ids],
            'default_voyage_number': self.voyage_number,
            'default_vessel_id': self.vessel_id.id,
            'default_shipping_line_id': self.shipping_line_id.id
        }

        return {
            'name': 'Master Shipment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.master.shipment',
            'context': default_shipment_vals
        }

    def copy_data(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        default['gross_weight_unit'] = self.gross_weight_unit
        default['gross_weight_unit_uom_id'] = self.gross_weight_unit_uom_id.id
        default['volume_unit'] = self.volume_unit
        default['weight_volume_unit'] = self.weight_volume_unit
        default['volume_unit_uom_id'] = self.volume_unit_uom_id.id
        if self.cargo_is_package_group:
            default['package_ids'] = [(0, 0, package.copy_data()[0]) for package in self.package_ids]
        default['weight_volume_unit_uom_id'] = self.weight_volume_unit_uom_id.id
        return super(FreightHouseShipment, self).copy_data(default)

    def action_send_by_email(self):
        template = self.env.ref('freight_management.email_template_send_by_email', False)
        docx_template = self.env.ref('freight_management.master_house_booking_confirmation_docx_template')
        attachment = self.env['ir.attachment'].create({
            'type': 'binary',
            'name': self.name,
            'res_model': 'mail.compose.message',
            'datas': base64.encodebytes(docx_template.render_document_report(self.ids)[0]),
        })
        compose_ctx = dict(
            default_model=self._name,
            default_res_ids=self.ids,
            default_use_template=bool(template.id),
            default_template_id=template.id,
            default_partner_ids=self.client_ids.ids,
            default_attachment_ids=attachment.ids,
            mail_tz=self.env.user.tz,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send Email'),
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': compose_ctx,
        }

    def action_attach_shipment_house(self):
        if self._context.get('default_parent_id'):
            self.write({'parent_id': self._context['default_parent_id']})
            self.parent_id.event_ids.attach_event_to_house()
        self.notify_user('House Attached', '{} House attached to Master Shipment-{}'.format(','.join(self.mapped('booking_nomination_no')), self[0].parent_id.name), 'success')

    def action_detach_shipment_house(self):
        for house_shipment in self:
            # Removed Packages fetched from House Shipment
            fetched_packs = house_shipment.parent_id.package_ids.filtered(lambda p: p.house_shipment_pack_id and p.house_shipment_pack_id.shipment_id.id == house_shipment.id)
            if fetched_packs:
                fetched_packs.unlink()
            # Removed Containers fetched from House Shipment
            fetched_containers = house_shipment.parent_id.container_ids.filtered(lambda p: p.house_shipment_pack_id and p.house_shipment_pack_id.shipment_id.id == house_shipment.id)
            if fetched_containers:
                fetched_containers.unlink()

            # Removed Master Shipment Event from Detached House
            house_shipment_event_ids = house_shipment.event_ids.filtered(
                lambda event: event.master_shipment_event_id and event.master_shipment_id == house_shipment.parent_id)
            house_shipment_event_ids and house_shipment_event_ids.unlink()

        self.notify_user('House Detached', '{} House detached from Master Shipment.'.format(','.join(self.mapped('booking_nomination_no'))), 'success')
        self.write({'parent_id': False})

    # Common Method to be Use in FCL/LCL File Download or Upload Start
    def xls_decimal_data_validation(self):
        return {
            'validate': 'decimal',
            'criteria': '>=',
            'value': 0,
            'error_message': 'Only numeric values are allowed'
        }

    def _ISO_validate_container_number(self, container_number):
        return True

    def get_uom_id_by_name(self, uom_name, uom_category=False):
        '''Returns Default UoM Configured throughout system when Given UoM not found and UoMCategory received
        NOTE: Providing option to return default UoM based on uom_category to resolved case when Given UoM not found But UoM is mandatory field'''
        default_uom_mapping = {
            'weight': self.env.company.weight_uom_id.id,
            'volume': self.env.company.volume_uom_id.id,
            'pack': self.env.company.pack_uom_id.id,
            'dimension': self.env.company.dimension_uom_id.id,
        }
        uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
        if not uom and uom_category:
            return default_uom_mapping[uom_category]
        return uom and uom.id or False

    def get_package_uom_value(self, domain):
        uom_ids = self.env['uom.uom'].search(domain)
        return uom_ids.mapped('name')

    def get_haz_class_id_by_name(self, haz_class_name):
        return self.env['haz.sub.class.code'].search([('name', '=', haz_class_name)], limit=1).id

    def check_boolean_value(self, value):
        if value and str(value).isdigit():
            value = bool(int(value))
        elif value:
            value = bool(str(value).lower())
        else:
            value = False
        return value

    # Method to be Use in FCL/LCL File Download or Upload Ends
    def check_uom_values(self, data, skip_blank=True):
        for num in range(len(data) - 1):
            current_values = data[num].split('_')
            next_values = data[num + 1].split('_')
            for i in range(3):
                if not skip_blank and (current_values[i] == 'False' or next_values[i] == 'False'):
                    return False
                if current_values[i] != 'False' and next_values[i] != 'False' and current_values[i] != next_values[i]:
                    return False
        return True

    @api.depends('container_ids', 'container_ids.container_number', 'container_ids.container_number.container_number',
                 'package_ids', 'package_ids.container_number', 'package_ids.container_number.container_number')
    def cal_container_number(self):
        for rec in self:
            packaging_mode = 'container' if rec.cargo_type_id and not rec.cargo_type_id.is_package_group else 'package'
            if packaging_mode == 'package':
                rec.container_number = ', '.join(rec.mapped('package_ids.container_number.container_number'))
            else:
                rec.container_number = ', '.join(rec.mapped('container_ids.container_number.container_number'))

    @api.depends('container_ids', 'container_ids.container_type_id', 'container_ids.container_type_id.name',
                 'package_ids', 'package_ids.container_type_id', 'package_ids.container_type_id.name')
    def cal_container_type(self):
        for rec in self:
            packaging_mode = 'container' if rec.cargo_type_id and not rec.cargo_type_id.is_package_group else 'package'
            if packaging_mode == 'package':
                container_types = []
                for package in rec.package_ids:
                    if package.container_type_id:
                        container_types.append('[{}] {}'.format(package.container_type_id.code, package.container_type_id.name))
                rec.container_type = ', '.join(container_types)
            else:
                container_types = []
                for container in rec.container_ids:
                    if container.container_type_id:
                        container_types.append('[{}] {}'.format(container.container_type_id.code, container.container_type_id.name))
                rec.container_type = ', '.join(container_types)

    @api.depends('commercial_invoice', 'lc_number')
    def _compute_updated_on_datetime(self):
        """
        Set current datetime for change of the commercial_invoice and lc_number field changes.
        If any of the fields will empty then black their related datetime field.
        """
        commercial_invoice_updated_on = False
        lc_number_updated_on = False
        for house_ship in self:
            if house_ship.commercial_invoice:
                commercial_invoice_updated_on = fields.Datetime.now()
            if house_ship.lc_number:
                lc_number_updated_on = fields.Datetime.now()
            house_ship.commercial_invoice_updated_on = commercial_invoice_updated_on
            house_ship.lc_number_updated_on = lc_number_updated_on
