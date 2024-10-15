# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.addons.odoo_base import tools
from odoo.osv import expression
from odoo.tools.misc import formatLang
from datetime import datetime
from odoo.exceptions import ValidationError

READONLY_STAGE = {'draft': [('readonly', False)]}
STATES = [
    ('draft', 'Draft'),
    ('sent', 'Sent'),
    ('expire', 'Expired'),
    ('cancel', 'Cancelled'),
    ('accept', 'Accepted'),
    ('reject', 'Rejected')
]


class ShipmentQuote(models.Model):
    _name = "shipment.quote"
    _inherit = [
        'mail.thread', 'mail.activity.mixin', 'portal.mixin', 'image.mixin',
        'freight.base.company.user.mixin', 'freight.customer.mixin', 'freight.shipper.mixin', 'freight.consignee.mixin', 'freight.product.mixin', 'freight.cargo.weight.volume.mixin',
    ]
    _description = "Quote"
    _order = "date desc, create_date desc, id desc"
    _segment_key = 'quotations'

    @api.depends('is_courier_shipment')
    def _compute_shipment_type_domain(self):
        for rec in self:
            domain = ['|', ('is_courier_shipment', '=', False), ('is_courier_shipment', '=', rec.is_courier_shipment)]
            rec.shipment_type_domain = json.dumps(domain)

    shipment_type_domain = fields.Char(compute='_compute_shipment_type_domain', store=True)

    @api.depends('transport_mode_id', 'shipment_type_id', 'cargo_type_id')
    def _compute_shipment_quote_template_id(self):
        for quote in self:
            shipment_quote_template_id = False
            shipment_quote_template_ids = self.env['shipment.quote.template'].search([
                ('transport_mode_id', '=', quote.transport_mode_id.id),
                ('shipment_type_id', '=', quote.shipment_type_id.id),
                ('cargo_type_ids', 'in', quote.cargo_type_id.ids),
                ('template_for', '=', 'shipment'),
            ], order="id desc", limit=1)

            if shipment_quote_template_ids:
                shipment_quote_template_id = shipment_quote_template_ids[0].id
            quote.shipment_quote_template_id = shipment_quote_template_id

    def get_template_domain(self):
        self.ensure_one()
        return json.dumps([('template_for', '=', 'shipment'), ('transport_mode_id', '=', self.transport_mode_id.id),
                           ('shipment_type_id', '=', self.shipment_type_id.id), ('cargo_type_ids', 'in', self.cargo_type_id.id)])

    @api.depends('quote_for', 'transport_mode_id', 'shipment_type_id', 'cargo_type_id')
    def _compute_quote_template_domain(self):
        for quote in self:
            quote.quote_template_domain = quote.get_template_domain()

    def _expand_states(self, states, domain, order):
        return [key for key, dummy in type(self).state.selection]

    @api.depends('transport_mode_id', 'destination_country_id')
    def _compute_port_of_discharge_domain(self):
        for rec in self:
            domain = ['|', ('country_id', '=', rec.destination_country_id.id), ('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.port_of_discharge_domain = json.dumps(domain)

    port_of_discharge_domain = fields.Char(compute='_compute_port_of_discharge_domain', store=True)

    @api.depends('transport_mode_id', 'origin_country_id')
    def _compute_port_of_loading_domain(self):
        for rec in self:
            domain = ['|', ('country_id', '=', rec.origin_country_id.id), ('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.port_of_loading_domain = json.dumps(domain)

    port_of_loading_domain = fields.Char(compute='_compute_port_of_loading_domain', store=True)

    @api.depends('transport_mode_id')
    def _compute_carrier_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.carrier_domain = json.dumps(domain)

    carrier_domain = fields.Char(compute='_compute_carrier_domain', store=True)

    name = fields.Char(
        string='Quotation Number',
        required=True,
        copy=False,
        readonly=True,
        states=READONLY_STAGE,
        index=True,
        default='New Quotation',
        store=True
    )
    date = fields.Date(default=lambda self: fields.Date.today(), states=READONLY_STAGE, readonly=True, copy=False)
    quote_expiry_date = fields.Date(states=READONLY_STAGE, readonly=True, copy=False)
    state = fields.Selection(STATES, string="Status", default='draft', tracking=True, group_expand='_expand_states')
    company_id = fields.Many2one('res.company', states=READONLY_STAGE, readonly=True)
    user_id = fields.Many2one('res.users', string="Sales Agent", states=READONLY_STAGE, tracking=True)
    country_id = fields.Many2one('res.country', states=READONLY_STAGE, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Local Currency', readonly=True)
    opportunity_id = fields.Many2one('crm.prospect.opportunity', string='Opportunity')
    document_count = fields.Integer(compute='_compute_document_count')
    # Client Details
    client_id = fields.Many2one('res.partner', states=READONLY_STAGE, readonly=True)
    client_address_id = fields.Many2one('res.partner', states=READONLY_STAGE, readonly=True)
    shipper_id = fields.Many2one('res.partner', states=READONLY_STAGE, readonly=True)
    shipper_address_id = fields.Many2one('res.partner', states=READONLY_STAGE, readonly=True)
    consignee_id = fields.Many2one('res.partner', states=READONLY_STAGE, readonly=True)
    consignee_address_id = fields.Many2one('res.partner', states=READONLY_STAGE, readonly=True)

    # Mode of Shipment
    transport_mode_id = fields.Many2one('transport.mode', states=READONLY_STAGE, readonly=True, copy=False)
    shipment_type_id = fields.Many2one('shipment.type', states=READONLY_STAGE, readonly=True, copy=False)
    cargo_type_id = fields.Many2one('cargo.type', states=READONLY_STAGE, readonly=True, copy=False)
    consolidation_type_id = fields.Many2one('consolidation.type', states=READONLY_STAGE, readonly=True)

    # General Information
    service_mode_id = fields.Many2one('freight.service.mode', string='Service Mode', states=READONLY_STAGE, readonly=True)
    transit_time = fields.Char(string='Transit Time', states=READONLY_STAGE, readonly=True)
    estimated_pickup = fields.Datetime(string='Estimated Pickup', states=READONLY_STAGE, readonly=True)

    destination_un_location_id = fields.Many2one('freight.un.location', states=READONLY_STAGE, readonly=True, string="Destination")
    destination_country_id = fields.Many2one("res.country", string="Destination/Delivery Country", states=READONLY_STAGE, readonly=True)
    port_of_discharge_id = fields.Many2one("freight.port", string="Destination Port/AirPort", states=READONLY_STAGE, readonly=True)
    expected_delivery = fields.Datetime(string='Expected Delivery', states=READONLY_STAGE, readonly=True)
    reference_number = fields.Char(string='Reference Number', states=READONLY_STAGE, readonly=True)
    carrier_id = fields.Many2one('freight.carrier', string='Shipping Line', states=READONLY_STAGE, readonly=True)
    incoterm_id = fields.Many2one('account.incoterms', string='Incoterms', states=READONLY_STAGE, readonly=True)

    origin_un_location_id = fields.Many2one('freight.un.location', states=READONLY_STAGE, readonly=True, string="Origin")
    origin_country_id = fields.Many2one("res.country", string="Origin/Pickup Country", states=READONLY_STAGE, readonly=True)
    port_of_loading_id = fields.Many2one("freight.port", string="Origin Port/AirPort", states=READONLY_STAGE, readonly=True)
    source = fields.Selection([
        ('system', 'System'),
        ('customer', 'Customer'),
    ], default='system', string='Source')

    # Additional Services
    product_ids = fields.Many2many('product.product', string='Additional Services', states=READONLY_STAGE, readonly=True,
                                   domain=lambda self: [('categ_id', '=', self.env.ref('freight_base.shipment_other_charge_category').id)])
    agent_id = fields.Many2one('res.partner', states=READONLY_STAGE,
                               readonly=True, domain=lambda self: [('category_ids', 'in', self.env.ref('freight_base.org_type_agent').ids)])
    agent_address_id = fields.Many2one('res.partner', states=READONLY_STAGE, readonly=True,
                                       domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('parent_id', '=', agent_address_id), ('id', '=', agent_address_id)]")
    co_loader_id = fields.Many2one('res.partner', string='CoLoader', states=READONLY_STAGE, readonly=True,
                                   domain=lambda self: [('category_ids', 'in', self.env.ref('freight_base.org_type_co_loader').ids)])
    co_loader_address_id = fields.Many2one('res.partner', string='CoLoader Address', states=READONLY_STAGE, readonly=True,
                                           domain="[\
                                               '|', \
                                                   ('company_id', '=', False), \
                                                   ('company_id', '=', company_id), \
                                                '|', \
                                                    ('parent_id', '=', co_loader_address_id), \
                                                    ('id', '=', co_loader_address_id)\
                                                ]")
    free_day = fields.Char(string='Free Day')

    # Monetary Details
    goods_value = fields.Monetary(string='Goods Value', currency_field='goods_value_currency_id',
                                  states=READONLY_STAGE, readonly=True)
    goods_value_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id,
                                              states=READONLY_STAGE, readonly=True)
    insurance_value = fields.Monetary(string='Insurance Value', currency_field='insurance_value_currency_id',
                                      states=READONLY_STAGE, readonly=True)
    insurance_value_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id,
                                                  states=READONLY_STAGE, readonly=True)

    # Weight/Volume
    pack_unit = fields.Integer(states=READONLY_STAGE, readonly=True)
    pack_unit_uom_id = fields.Many2one('uom.uom', states=READONLY_STAGE, readonly=True)

    gross_weight_unit = fields.Float(states=READONLY_STAGE, readonly=True, compute='_compute_auto_update_weight_volume', store=True)
    gross_weight_unit_uom_id = fields.Many2one('uom.uom', 'Gross Weight UoM', states=READONLY_STAGE, readonly=True)

    net_weight_unit = fields.Float(states=READONLY_STAGE, readonly=True, compute='_compute_auto_update_weight_volume', store=True)
    net_weight_unit_uom_id = fields.Many2one('uom.uom', states=READONLY_STAGE, readonly=True)

    volume_unit = fields.Float(states=READONLY_STAGE, readonly=True, compute='_compute_auto_update_weight_volume', store=True)
    volume_unit_uom_id = fields.Many2one('uom.uom', states=READONLY_STAGE, readonly=True)

    weight_volume_unit = fields.Float(states=READONLY_STAGE, readonly=True, compute='_compute_auto_update_weight_volume', store=True)
    weight_volume_unit_uom_id = fields.Many2one('uom.uom', states=READONLY_STAGE, readonly=True)

    chargeable = fields.Float(string='Chargeable', compute='_compute_chargeable', store=True, readonly=True)
    chargeable_uom_id = fields.Many2one('uom.uom', states=READONLY_STAGE, readonly=True)
    # Containers
    quote_container_line_ids = fields.One2many('shipment.quote.container.lines', 'quotation_id', states=READONLY_STAGE, readonly=True)

    # Loose Cargo
    quote_cargo_line_ids = fields.One2many('shipment.quote.cargo.lines', 'quotation_id', states=READONLY_STAGE, readonly=True)

    # Quote Charge
    quotation_line_ids = fields.One2many('shipment.quote.line', 'quotation_id', string="Quote Charges", states=READONLY_STAGE, readonly=True)
    estimated_total_cost = fields.Monetary(string='Estimated Total Cost', compute='_compute_estimated_total_cost', currency_field='currency_id')
    estimated_total_revenue = fields.Monetary(string='Estimated Total Revenue', compute='_compute_estimated_total_revenue', currency_field='currency_id')
    estimated_profit = fields.Monetary(string='Estimated Profit', compute='_compute_estimated_profit', currency_field='currency_id')
    estimated_margin_percent = fields.Float(string='Estimated Margin Percent', compute='_compute_estimated_margin_percent')

    is_dangerous_good = fields.Boolean('HAZ?', states=READONLY_STAGE, readonly=True)
    dangerous_good_note = fields.Text("HAZ Remark", states=READONLY_STAGE, readonly=True)
    remarks = fields.Text("Remarks", states=READONLY_STAGE, readonly=True)
    is_package_group = fields.Boolean(string="Package Group", related='cargo_type_id.is_package_group', store=True)
    auto_update_weight_volume = fields.Boolean('Auto Update Weight & Volume', states=READONLY_STAGE, readonly=True)
    quote_template_domain = fields.Char(compute='_compute_quote_template_domain')
    shipment_quote_template_id = fields.Many2one('shipment.quote.template',
                                                 compute="_compute_shipment_quote_template_id",
                                                 string='Template',
                                                 store=True,
                                                 states=READONLY_STAGE, readonly=True)
    note = fields.Html('Terms and conditions', states=READONLY_STAGE, readonly=True)
    freight_shipment_ids = fields.One2many('freight.house.shipment', 'shipment_quote_id')
    freight_shipment_count = fields.Integer(compute='_compute_freight_shipment', store=True)
    freight_direct_shipment_count = fields.Integer(compute='_compute_freight_direct_shipment_count', store=False)
    freight_shipment_type = fields.Selection([
        ('house_shipment', 'House Shipment'),
        ('master_shipment', 'Direct Shipment')
    ], compute='_compute_freight_shipment_type', store=False, string='Shipment Type')
    cancelled_quote_id = fields.Many2one('shipment.quote', string='Previous Quote', copy=False)
    revised_in_quote_ids = fields.One2many('shipment.quote', 'cancelled_quote_id', string='Revised In')
    route_ids = fields.One2many('freight.quote.route', 'quote_id', string='Routes')
    enable_quote_routing = fields.Boolean(string="Enable Quote Routing", related='company_id.enable_quote_routing', store=True)
    image_1920 = fields.Image("Signature", max_width=1920, max_height=1920, copy=False)
    document_ids = fields.One2many('freight.quote.document', 'quote_id', string='Documents')
    signed_by = fields.Char('Signed By', help='Name of the person that signed the Quote.', copy=False)
    signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
    change_reason_id = fields.Many2one('change.reason', string="Change Reason")
    show_incl_single_line = fields.Boolean('Show All Incl. in Single line', default=False, states=READONLY_STAGE, readonly=True)
    decline_message = fields.Text("decline_message")
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    flight_number = fields.Char('Flight Number', states=READONLY_STAGE, readonly=True, copy=False)
    aircraft_type = fields.Selection([
        ('coa', 'COA'),
        ('pax', 'PAX')
    ], copy=False, states=READONLY_STAGE, readonly=True, default='coa')

    # Docx Report Field
    include_total_amount = fields.Monetary(compute='_compute_report_all_includes_fields', store=True)
    include_total_amount_in_words = fields.Char(compute='_compute_include_total_amount_in_word', store=True)
    all_include_sell_amount_rate = fields.Monetary(compute='_compute_report_all_includes_fields', store=True)
    include_tax_names = fields.Char(compute='_compute_report_all_includes_fields', store=True)
    origin_port_name = fields.Char(related='port_of_loading_id.name', store=True)
    destination_port_name = fields.Char(related='port_of_discharge_id.name', store=True, string='Destination Port Name')
    is_courier_shipment = fields.Boolean(string='Courier Shipment')
    quote_for = fields.Selection([
        ('shipment', 'Shipment')
    ], default='shipment')
    shipment_count = fields.Selection([
        ('single', 'Single'), ('multiple', 'Multiple')
    ], default='single', tracking=True)

    # team
    team_id = fields.Many2one(
        'crm.prospect.team', 'Sales Team',
        ondelete="restrict", tracking=True,
        check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    haz_class_id = fields.Many2one('haz.sub.class.code', 'HAZ Class', states=READONLY_STAGE, readonly=True)
    haz_un_number = fields.Char('UN #', states=READONLY_STAGE, readonly=True)
    # Address Fields
    pickup_address = fields.Text('Pickup Address')
    delivery_address = fields.Text('Delivery Address')
    incoterm_check = fields.Boolean(related='incoterm_id.incoterm_check')
    quote_check = fields.Boolean('Quote Check', compute='_compute_quote_check')
    shipper_consignee_bool = fields.Boolean('Shipper/Consignee', compute='_compute_shipper_consignee_quote')
    chargeable_volume = fields.Float('Chargeable Volume', store=True, compute='_compute_chargeable_volume')
    chargeable_volume_unit_uom_id = fields.Many2one('uom.uom', states=READONLY_STAGE, readonly=True)
    total_teu = fields.Integer(compute='_compute_total_teu', store=True)

    _sql_constraints = [
        ('name_unique', 'CHECK(1=1)', 'IGNORE')
    ]

    @api.depends('quote_container_line_ids', 'quote_container_line_ids.teu')
    def _compute_total_teu(self):
        for rec in self:
            rec.total_teu = sum(rec.quote_container_line_ids.mapped('teu'))

    @api.depends('quote_cargo_line_ids',
                 'auto_update_weight_volume',
                 'quote_cargo_line_ids.weight',
                 'quote_cargo_line_ids.volume',
                 'quote_cargo_line_ids.lwh_uom_id',
                 'quote_cargo_line_ids.chargeable_volume',
                 'quote_cargo_line_ids.volumetric_weight')
    def _compute_chargeable_volume(self):
        volumetric_divided_value_ids = self.env['volumetric.divided.value']
        for quote in self:
            if quote.opportunity_id and quote.quote_cargo_line_ids:
                for cargo in quote.quote_cargo_line_ids:
                    if cargo.transport_mode_id and cargo.lwh_uom_id and cargo.mode_type == 'sea':
                        volumetric_divided_value = volumetric_divided_value_ids.search([
                            ('transport_mode_id', '=', cargo.transport_mode_id.id),
                            ('uom_id', '=', cargo.lwh_uom_id.id)])
                        cargo.divided_value = volumetric_divided_value.divided_value
                        if cargo.divided_value:
                            if cargo.lwh_uom_id:
                                cargo.volume = (cargo.count * cargo.length * cargo.width * cargo.height) / cargo.divided_value
                                if cargo.weight:
                                    weight = (cargo.weight / 1000)
                                    cargo.chargeable_volume = max(cargo.volume, weight)
                                else:
                                    cargo.chargeable_volume = 0.0
                            else:
                                cargo.volume = 0.0
                        else:
                            cargo.divided_value = 0.0

            if quote.auto_update_weight_volume:
                quote.chargeable_volume = sum(quote.quote_cargo_line_ids.mapped('chargeable_volume'))
                quote.chargeable_volume_unit_uom_id = quote.quote_cargo_line_ids.mapped('chargeable_uom_id')

    @api.depends('company_id')
    def _compute_shipper_consignee_quote(self):
        shipper_consignee_bool = self.env['ir.config_parameter'].sudo().get_param(
            'freight_management.shipper_consignee_non_mandatory')
        for rec in self:
            if shipper_consignee_bool:
                rec.shipper_consignee_bool = True
            else:
                rec.shipper_consignee_bool = False

    @api.onchange('chargeable_volume', 'quotation_line_ids')
    def _onchange_chargeable_volume(self):
        if self.chargeable_volume:
            weight_measurement = self.env.ref('freight_base.measurement_basis_wm')
            measurement = self.quotation_line_ids.filtered(lambda c: c.measurement_basis_id.id == weight_measurement.id)
            measurement.quantity = self.chargeable_volume

    @api.onchange('agent_id')
    def _onchange_agent_id(self):
        if self.agent_id:
            self.agent_address_id = self.agent_id

    @api.onchange('co_loader_id')
    def _onchange_co_loader_id(self):
        if self.co_loader_id:
            self.co_loader_address_id = self.co_loader_id

    @api.depends('company_id')
    def _compute_quote_check(self):
        is_quote_check = self.env['ir.config_parameter'].sudo().get_param('freight_management.enable_non_mandatory_fields')
        for rec in self:
            if is_quote_check:
                rec.quote_check = True
            else:
                rec.quote_check = False

    @api.onchange('team_id')
    def onchange_team_id(self):
        if not self.opportunity_id:
            if self.env.user not in self.team_id.member_ids:
                self.user_id = False
            elif self.env.user in self.team_id.member_ids or self.env.user in self.team_id.user_id:
                self.user_id = self.env.user.id
        return {'domain': {'user_id': [('id', 'in', self.team_id.member_ids.ids + self.team_id.user_id.ids)]}}

    @api.onchange('pack_unit')
    def check_pack_unit(self):
        for rec in self:
            if rec.pack_unit < 0:
                raise ValidationError('Pack Unit should not be negative.')

    @api.constrains('port_of_loading_id', 'port_of_discharge_id')
    def _check_origin_destination_port(self):
        for rec in self:
            if rec.port_of_loading_id and rec.port_of_discharge_id and rec.port_of_loading_id == rec.port_of_discharge_id:
                raise ValidationError(_('Origin and Destination Port/Airport Must be Different, It can not same.'))

    @api.constrains('gross_weight_unit', 'net_weight_unit', 'gross_weight_unit_uom_id', 'net_weight_unit_uom_id')
    def _check_gross_net_weight_unit(self):
        for rec in self:
            net_weight = rec.net_weight_unit_uom_id._compute_quantity(rec.net_weight_unit, rec.gross_weight_unit_uom_id)
            if rec.gross_weight_unit < net_weight:
                raise ValidationError(_('The Net weight should not be greater than the Gross weight.'))

    @api.depends('quotation_line_ids', 'quotation_line_ids.tax_ids', 'show_incl_single_line', 'quotation_line_ids.total_sell_amount', 'quotation_line_ids.include_charges')
    def _compute_report_all_includes_fields(self):
        for rec in self:
            sell_amount_rate = 0.0
            for line in rec.quotation_line_ids:
                sell_amount_rate += round(line.sell_amount_rate * (line.sell_conversion_rate or 1), 3)
            rec.all_include_sell_amount_rate = sell_amount_rate
            rec.include_tax_names = ",".join(rec.quotation_line_ids.mapped('tax_ids').mapped('name'))
            if rec.show_incl_single_line:
                rec.include_total_amount = round(sum(rec.quotation_line_ids.mapped('total_sell_amount')), 3)
            else:
                include_charge_line = rec.quotation_line_ids.filtered(lambda line: line.include_charges)
                rec.include_total_amount = round(sum(include_charge_line.mapped('total_sell_amount')), 3)

    @api.depends('include_total_amount')
    def _compute_include_total_amount_in_word(self):
        for rec in self:
            rec.include_total_amount_in_words = '{} Only'.format(rec.currency_id.amount_to_text(rec.include_total_amount))

    @api.constrains('shipment_quote_template_id', 'transport_mode_id', 'shipment_type_id', 'cargo_type_id', 'quote_for')
    def _check_shipment_quote_template_id(self):
        for order in self.filtered(lambda quote: quote.shipment_quote_template_id and quote.quote_for == 'shipment'):
            invalid = False
            if order.shipment_quote_template_id.transport_mode_id != order.transport_mode_id:
                invalid = True
            if order.shipment_quote_template_id.shipment_type_id != order.shipment_type_id:
                invalid = True
            if order.cargo_type_id not in order.shipment_quote_template_id.cargo_type_ids:
                invalid = True
            if invalid:
                raise ValidationError(_("The selected template must have the same "
                                        "Transport Mode, Shipment Type, and Cargo Type as the quote."))

    @api.constrains('quote_expiry_date')
    def _check_quote_expiry_date(self):
        for rec in self:
            if not self.env.context.get('_ignore_constraint_check', False) and rec.quote_expiry_date and rec.quote_expiry_date < datetime.today().date():
                raise ValidationError("Please select today's date or a future date for the Quote Expiry Date.")

    @api.constrains('company_id')
    def _check_change_company(self):
        for rec in self:
            if rec.company_id and rec.quotation_line_ids and rec.quotation_line_ids.filtered(lambda q: q.company_id.id != rec.company_id.id):
                raise ValidationError(_('You can not change company once charges are added'))

    @api.model_create_single
    def create(self, values):
        rec = super().create(values)
        rec._update_documents_list()
        return rec

    def charges_visibility_to_customer(self):
        ''' Customer portal charge type view'''
        quote_line = self.quotation_line_ids
        if self.show_incl_single_line and quote_line:
            return [{
                'display_name': 'Inclusive all charges',
                'quantity': sum(quote_line.mapped('quantity')),
                'tax_ids': ','.join([line.name for line in quote_line.mapped('tax_ids')]),
                'total_sell_amount': sum(quote_line.mapped('total_sell_amount')),
                'symbol': 'Symbol',
                'cost_amount_rate': sum(quote_line.mapped('cost_amount_rate')),
                'sell_amount_rate': sum(quote_line.mapped('sell_amount_rate'))}]
        else:
            return [({
                'display_name': line.service_name,
                'quantity': line.quantity,
                'tax_ids': ','.join([tax.name for tax in line.tax_ids]),
                # 'total_sell_amount': formatLang(self.env,  line.total_sell_amount, currency_obj=line.currency_id),
                'total_sell_amount': formatLang(self.env,  line.sell_amount_rate * line.quantity if line.sell_currency_mismatch else line.total_sell_amount, currency_obj=line.sell_currency_id),
                'cost_amount_rate': formatLang(self.env, line.cost_amount_rate, currency_obj=line.cost_currency_id),
                'sell_amount_rate': formatLang(self.env, line.sell_amount_rate, currency_obj=line.sell_currency_id)})
                for line in quote_line.filtered(lambda line: line.include_charges)]

    def _update_documents_list(self):
        self.ensure_one()
        document_types = self.env['freight.document.type'].sudo().search([('model_id.model', '=', self._name)])
        documents = [(0, 0, {
            'name': doc_type.name,
            'document_type_id': doc_type.id,
            'datetime': self.create_date
        }) for doc_type in document_types]
        self.write({'document_ids': documents})

    @api.depends('freight_shipment_ids', 'freight_shipment_ids.state')
    def _compute_freight_shipment(self):
        for quote in self:
            quote.freight_shipment_count = len(quote.freight_shipment_ids.filtered(lambda s: s.state != 'cancelled'))

    @api.depends('freight_shipment_ids', 'freight_shipment_ids.state')
    def _compute_freight_shipment_type(self):
        for quote in self:
            hs_count = quote.freight_shipment_count
            ms_count = quote.freight_direct_shipment_count
            if ms_count > 0:
                shipment_type = 'master_shipment'
            elif hs_count > 0:
                shipment_type = 'house_shipment'
            else:
                shipment_type = None
            quote.freight_shipment_type = shipment_type

    @api.depends('freight_shipment_ids', 'freight_shipment_ids.state')
    def _compute_freight_direct_shipment_count(self):
        for quote in self:
            quote.freight_direct_shipment_count = len(quote.freight_shipment_ids.mapped('parent_id').filtered(lambda s: s.state != 'cancelled'))

    @api.onchange('shipment_quote_template_id')
    def _onchange_shipment_quote_template_id(self):
        self.note = False
        if self.shipment_quote_template_id:
            self.note = self.shipment_quote_template_id.body_html

    @api.depends(
        'auto_update_weight_volume', 'cargo_is_package_group',
        'quote_container_line_ids',
        'quote_cargo_line_ids', 'quote_cargo_line_ids.weight', 'quote_cargo_line_ids.weight_uom_id', 'quote_cargo_line_ids.volume', 'quote_cargo_line_ids.volume_uom_id',
        'quote_cargo_line_ids.volumetric_weight')
    def _compute_auto_update_weight_volume(self):
        volume_uom = self.env.company.volume_uom_id
        weight_uom = self.env.company.weight_uom_id
        package_uom = self.env.ref('freight_base.pack_uom_pkg')

        for quote in self:
            # Keep Manual value when No auto update
            if not quote.auto_update_weight_volume or not quote.cargo_is_package_group:
                quote.gross_weight_unit = quote.gross_weight_unit
                quote.weight_volume_unit = quote.weight_volume_unit
                quote.volume_unit = quote.volume_unit
                quote.gross_weight_unit_uom_id = quote.gross_weight_unit_uom_id
                quote.weight_volume_unit_uom_id = quote.weight_volume_unit_uom_id
                quote.volume_unit_uom_id = quote.volume_unit_uom_id
                quote.pack_unit = quote.pack_unit
                quote.pack_unit_uom_id = quote.pack_unit_uom_id
            else:
                total_gross_weight = sum([p.weight_uom_id._compute_quantity(p.weight, weight_uom) for p in quote.quote_cargo_line_ids])
                total_volumetric_weight_unit = sum([p.weight_uom_id._compute_quantity(p.volumetric_weight, weight_uom) for p in quote.quote_cargo_line_ids])
                total_volume_unit = sum(quote.quote_cargo_line_ids.mapped('volume'))
                pack_unit = sum(quote.quote_cargo_line_ids.mapped('count'))
                package_uom = quote.quote_cargo_line_ids.mapped('pack_type_id') if len(quote.quote_cargo_line_ids.mapped('pack_type_id')) == 1 else package_uom

                quote.gross_weight_unit, quote.gross_weight_unit_uom_id = round(total_gross_weight, 3), weight_uom.id
                quote.weight_volume_unit, quote.weight_volume_unit_uom_id = round(total_volumetric_weight_unit, 3), weight_uom.id
                quote.volume_unit, quote.volume_unit_uom_id = round(total_volume_unit, 3), volume_uom.id
                quote.pack_unit, quote.pack_unit_uom_id = round(pack_unit, 3), package_uom.id

    @api.depends('gross_weight_unit', 'gross_weight_unit_uom_id', 'net_weight_unit', 'net_weight_unit_uom_id', 'weight_volume_unit', 'weight_volume_unit_uom_id', 'chargeable_uom_id')
    def _compute_chargeable(self):
        for quote in self:
            chargeable_uom = quote.chargeable_uom_id
            gross_weight = quote.gross_weight_unit_uom_id._compute_quantity(quote.gross_weight_unit, chargeable_uom)
            net_weight = quote.net_weight_unit_uom_id._compute_quantity(quote.net_weight_unit, chargeable_uom)
            weight_volume = quote.weight_volume_unit_uom_id._compute_quantity(quote.weight_volume_unit, chargeable_uom)
            quote.chargeable = round(max(gross_weight, net_weight, weight_volume, 0), 3)

    @api.onchange('gross_weight_unit')
    def _onchange_gross_weight_unit(self):
        if self.gross_weight_unit:
            weight = self.env.ref('freight_base.measurement_basis_weight')
            number_unit = self.quotation_line_ids.filtered(lambda s: s.measurement_basis_id.id == weight.id)
            number_unit.quantity = self.gross_weight_unit

    @api.onchange('volume_unit')
    def _onchange_volume_unit(self):
        if self.volume_unit:
            volume = self.env.ref('freight_base.measurement_basis_volume')
            number_unit = self.quotation_line_ids.filtered(lambda s: s.measurement_basis_id.id == volume.id)
            number_unit.quantity = self.volume_unit

    @api.onchange('chargeable')
    def _onchange_chargeable(self):
        if self.chargeable:
            charge = self.env.ref('freight_base.measurement_basis_chargeable')
            number_unit = self.quotation_line_ids.filtered(lambda s: s.measurement_basis_id.id == charge.id)
            number_unit.quantity = self.chargeable

    @api.depends('quotation_line_ids.total_cost_amount')
    def _compute_estimated_total_cost(self):
        for quote in self:
            quote.estimated_total_cost = round(sum(quote.quotation_line_ids.mapped('total_cost_amount')), 3)

    @api.depends('quotation_line_ids.total_sell_amount')
    def _compute_estimated_total_revenue(self):
        for quote in self:
            quote.estimated_total_revenue = round(sum(quote.quotation_line_ids.mapped('total_sell_amount')), 3)

    @api.depends('estimated_total_cost', 'estimated_total_revenue')
    def _compute_estimated_profit(self):
        for quote in self:
            quote.estimated_profit = quote.estimated_total_revenue - quote.estimated_total_cost

    @api.depends('estimated_profit', 'estimated_total_revenue')
    def _compute_estimated_margin_percent(self):
        for quote in self:
            if quote.estimated_total_revenue != 0:
                quote.estimated_margin_percent = (quote.estimated_profit * 100) / quote.estimated_total_revenue
            else:
                quote.estimated_margin_percent = 0.0

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        values = {'carrier_id': False}
        if self.opportunity_id and self.opportunity_id.transport_mode_id.id != self.transport_mode_id.id or not self.opportunity_id:
            values.update({'port_of_loading_id': False, 'port_of_discharge_id': False, 'cargo_type_id': False})
        else:
            values.update({'port_of_loading_id': self.opportunity_id.port_of_loading_id.id,
                           'port_of_discharge_id': self.opportunity_id.port_of_discharge_id.id,
                           'cargo_type_id': self.opportunity_id.cargo_type_id.id
                           })
        # if self.transport_mode_id.mode_type == 'land':
        #     values.update({'is_courier_shipment': False})
        self.update(values)

    @api.onchange('cargo_type_id')
    def _onchange_cargo_type_id(self):
        if not self.cargo_is_package_group:
            self.auto_update_weight_volume = False

    @api.onchange('origin_country_id')
    def _onchange_origin_country(self):
        if self.origin_country_id:
            if self.origin_un_location_id.country_id != self.origin_country_id:
                self.origin_un_location_id = False
                self.port_of_loading_id = False

    @api.onchange('date')
    def _onchange_quote_date(self):
        for rec in self:
            rec.quote_expiry_date = rec.date and fields.Date.add(rec.date, days=30) or False

    @api.onchange('destination_country_id')
    def _onchange_destination_country(self):
        if self.destination_country_id:
            if self.destination_un_location_id.country_id != self.destination_country_id:
                self.destination_un_location_id = False
                self.port_of_discharge_id = False

    @api.onchange('origin_country_id')
    def _onchange_origin_country_id(self):
        values = {}
        is_quote_check = self.env['ir.config_parameter'].sudo().get_param('freight_management.enable_non_mandatory_fields')
        if (self.opportunity_id and self.opportunity_id.port_of_loading_id.country_id.id != self.origin_country_id.id) or not self.opportunity_id:
            if is_quote_check:
                values.update({
                    'port_of_loading_id': self.opportunity_id.port_of_loading_id.id,
                })
            else:
                values.update({
                    'port_of_loading_id': False,
                })
        else:
            values.update({
                'port_of_loading_id': self.opportunity_id.port_of_loading_id.id,
            })
        self.update(values)

    @api.onchange('destination_country_id')
    def _onchange_destination_country_id(self):
        self.update({'port_of_discharge_id': False})
        is_quote_check = self.env['ir.config_parameter'].sudo().get_param('freight_management.enable_non_mandatory_fields')
        values = {}
        if (self.opportunity_id and self.opportunity_id.port_of_discharge_id.country_id.id != self.destination_country_id.id) or not self.opportunity_id:
            if is_quote_check:
                values.update({
                    'port_of_discharge_id': self.opportunity_id.port_of_discharge_id.id,
                })
            else:
                values.update({
                    'port_of_discharge_id': False,
                })
        else:
            values.update({
                'port_of_discharge_id': self.opportunity_id.port_of_discharge_id.id,
            })
        self.update(values)

    def action_change_status(self):
        self.ensure_one()
        return {
            'name': 'Change Status',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.shipment.quote.status',
            'context': {'default_quotation_id': self.id, 'default_state': self.state}
        }

    def _prepare_quote_container_package_vals(self):
        self.ensure_one()
        container_ids = []
        package_ids = []
        if self.is_package_group:
            for line in self.quote_cargo_line_ids:
                package_ids.append({
                    'package_mode': 'package',
                    'package_type_id': line.pack_type_id.id,
                    'quantity': line.count,
                    'hbl_description': line.notes,
                    'is_hazardous': line.is_hazardous,
                    'quote_cargo_line_id': line.id,
                    'commodity_ids': [(0, 0, {
                        'commodity_id': line.commodity_id.id,
                        'pieces': line.count,
                        'pack_uom_id': line.pack_type_id.id,
                        'volume_uom_id': line.volume_uom_id.id,
                        'volumetric_weight_uom_id': line.volumetric_weight_uom_id.id or self.env.company.weight_uom_id.id,
                        'gross_weight': line.weight,
                        'volume': line.volume,
                        'volumetric_weight': line.volumetric_weight,
                        'length': line.length,
                        'width': line.width,
                        'height': line.height,
                        'divided_value': line.divided_value,
                        'dimension_uom_id': line.lwh_uom_id.id,
                        'chargeable_volume': line.chargeable_volume,
                        'chargeable_volume_uom_id': line.chargeable_uom_id.id
                    })] if line.commodity_id else [],
                })
        else:
            for line in self.quote_container_line_ids:
                for container_row in range(line.count):
                    container_ids.append({
                        'package_mode': 'container',
                        'container_type_id': line.container_type_id.id,
                        'quote_container_line_id': line.id,
                        'volume_unit': 0.0,
                        'pack_count': self.pack_unit,
                    })
        return package_ids if self.is_package_group else container_ids

    def _prepare_quote_route_vals(self):
        route_ids = []
        for route in self.route_ids:
            route_data = {
                'name': route.name,
                'route_type': route.route_type,
                'transport_mode_id': route.transport_mode_id.id,
                'transport_mode_type': route.transport_mode_type,
                'from_location_id': route.from_location_id.id,
                'to_location_id': route.to_location_id.id,
                'carrier_id': route.carrier_id.id,
                'vessel_id': route.vessel_id.id,
                'obl_number': route.obl_number,
                'voyage_number': route.voyage_number,
                'etd_time': route.etd_time,
                'eta_time': route.eta_time,
                'atd_time': route.atd_time,
                'ata_time': route.ata_time,
                'empty_container': route.empty_container,
                'empty_container_reference': route.empty_container_reference,
                'carrier_transport_mode': route.carrier_transport_mode,
                'carrier_driver_name': route.carrier_driver_name,
                'carrier_vehicle_number': route.carrier_vehicle_number,
                'remarks': route.remarks,
                'flight_number': route.flight_number,
                'mawb_number': route.mawb_number
            }
            route_ids.append(route_data)
        return route_ids

    def _prepare_house_shipment_values(self):
        self.ensure_one()
        container_ids = []
        package_ids = []
        route_ids = []

        if self.route_ids:
            route_ids = [(0, 0, val) for val in self._prepare_quote_route_vals()]
        if self.is_package_group:
            package_ids = [(0, 0, val) for val in self._prepare_quote_container_package_vals()]
        else:
            container_ids = [(0, 0, val) for val in self._prepare_quote_container_package_vals()]

        default_shipment_vals = {
            'default_shipment_quote_id': self.id,
            'default_state': 'created',
            'default_company_id': self.company_id.id,
            'default_shipment_date': self.date,
            'default_transport_mode_id': self.transport_mode_id.id,
            'default_cargo_type_id': self.cargo_type_id.id,
            'default_shipment_type_id': self.shipment_type_id.id,
            'default_inco_term_id': self.incoterm_id.id,
            'default_service_mode_id': self.service_mode_id.id,
            'default_client_id': self.client_id.id,
            'default_client_address_id': self.client_address_id.id,
            'default_shipper_id': self.shipper_id.id,
            'default_shipper_address_id': self.shipper_address_id.id,
            'default_consignee_id': self.consignee_id.id,
            'default_consignee_address_id': self.consignee_address_id.id,
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
            'default_origin_port_un_location_id': self.port_of_loading_id.id,
            'default_destination_port_un_location_id': self.port_of_discharge_id.id,
            'default_is_insured': True if self.goods_value > 0 or self.insurance_value > 0 else False,
            'default_goods_value_amount': self.goods_value,
            'default_goods_value_currency_id': self.goods_value_currency_id.id,
            'default_insurance_value_amount': self.insurance_value,
            'default_insurance_value_currency_id': self.insurance_value_currency_id.id,
            'default_ownership_id': self.client_id.id,
            'default_origin_un_location_id': self.origin_un_location_id.id,
            'default_destination_un_location_id': self.destination_un_location_id.id,
            'default_is_hazardous': self.is_dangerous_good,
            'default_haz_remark': self.dangerous_good_note,
            'default_sales_agent_id': self.user_id.id,
            'default_package_ids': package_ids,
            'default_container_ids': container_ids,
            'default_is_courier_shipment': self.is_courier_shipment,
            'default_haz_class_id': self.haz_class_id.id,
            'default_haz_un_number': self.haz_un_number,
            'default_shipment_for': self.quote_for,
            'default_pickup_address': self.pickup_address,
            'default_delivery_address': self.delivery_address,
            'default_free_day': self.free_day,
            'default_route_ids': route_ids,
            'default_remarks': self.remarks,
        }
        if self.mode_type in ['air', 'sea']:
            default_shipment_vals.update({
                'default_etd_time': self.estimated_pickup,
                'default_eta_time': self.expected_delivery,
            })

        shipment_partners = []
        for partner_field, address_field, partner_type_name in [('agent_id', 'agent_address_id', 'Agent'),
                                                                ('co_loader_id', 'co_loader_address_id', 'CoLoader')]:
            partner_id = self[partner_field]
            address_id = self[address_field]
            if partner_id and address_id:
                # Fetch partner type id
                partner_type_id = self.env['res.partner.type'].search([('name', '=', partner_type_name)], limit=1)
                if partner_type_id:
                    shipment_partners.append((0, 0, {
                        'partner_id': partner_id.id,
                        'party_address_id': address_id.id,
                        'partner_type_id': partner_type_id.id,  # Ensure partner type id is set
                    }))

        # Update default values with shipment partners
        if shipment_partners:
            default_shipment_vals.update({'default_shipment_partner_ids': shipment_partners})

        if self.mode_type == 'air':
            default_shipment_vals.update({
                'default_voyage_number': self.flight_number,
                'default_aircraft_type': 'cao' if self.aircraft_type == 'coa' else self.aircraft_type,
                'default_shipping_line_id': self.carrier_id.id})
        return default_shipment_vals

    def action_create_direct_shipment(self):
        if not self.service_mode_id:
            raise ValidationError(_("Service Mode is mandatory in House Shipment.Please add it in Quote"))
        default_house_shipment_vals = self._prepare_house_shipment_values()
        house_shipment_vals = {k.split('default_')[1]: v for k, v in default_house_shipment_vals.items()}
        house_shipment_vals['is_direct_shipment'] = True
        house_shipment_id = self.env['freight.house.shipment'].create(house_shipment_vals)
        return house_shipment_id.action_create_master_shipment()

    def action_create_shipment(self):
        default_shipment_vals = self._prepare_house_shipment_values()
        return {
            'name': 'House Shipment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.house.shipment',
            'context': default_shipment_vals
        }

    def action_open_direct_shipments(self):
        return_vals = {
            'name': _('Master Shipment'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.master.shipment',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {'control_panel_class': 'house', 'create': False},
            'domain': [('id', 'in', self.freight_shipment_ids.mapped('parent_id').ids)]
        }
        if len(self.freight_shipment_ids.parent_id.ids) == 1:
            return_vals.update({
                'view_mode': 'form',
                'res_id': self.freight_shipment_ids.mapped('parent_id').ids[0],
                'domain': [('id', '=', self.freight_shipment_ids.mapped('parent_id').id)],
            })
        return return_vals

    def action_open_shipments(self):
        return_vals = {
            'name': _('House Shipment'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.house.shipment',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {'control_panel_class': 'house', 'create': False},
            'domain': [('id', 'in', self.freight_shipment_ids.ids)]
        }
        if len(self.freight_shipment_ids.ids) == 1:
            return_vals.update({
                'view_mode': 'form',
                'res_id': self.freight_shipment_ids.ids[0],
                'domain': [('id', '=', self.freight_shipment_ids[0].id)],
            })
        return return_vals

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Quote Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.quote.document',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('quote_id', 'in', self.ids)],
            'context': {'default_quote_id': self.id, 'search_default_group_by_mode': 1},
            'target': 'current',
        }

    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    def _update_quote_status(self, new_status, change_reason_id=None, remark=None):
        self.ensure_one()
        if self.state == 'accept' and new_status == 'sent':
            raise ValidationError(_("Accepted to sent not possible."))

        if self.freight_shipment_count:
            raise ValidationError(_("Once Shipment is Created, The Status cannot be changed."))

        if self.state == 'accept' and new_status == 'expire':
            raise ValidationError(_("Accepted to expired status change not possible."))

        if new_status == 'sent':
            return self.action_option_publish_confirm_wizard()

        self.write({'state': new_status})

        if self.state in ('cancel', 'reject'):
            change_status = """Quotation State changed to <strong>"%s"</strong> due to <strong>%s</strong>""" % (new_status, change_reason_id and change_reason_id.name or '')
            if remark:
                change_status += """<br/>Remarks: %s """ % (remark)
            self.message_post(body=_(change_status))

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        quote = super(ShipmentQuote, self.with_context(_ignore_freight_sequence=True, update_freight_sequence_dynamic=True)).copy(default=default)
        quote._onchange_quote_date()
        return quote

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('update_freight_sequence_dynamic'):
            field_name_lst = ['shipment_type_id', 'cargo_type_id', 'transport_mode_id']
            for rec in self.filtered(lambda quote: quote.quote_for == 'shipment'):
                rec.update_shipment_quote_sequence(vals, field_name_lst)
        return res

    def update_shipment_quote_sequence(self, vals, field_name_lst):
        freight_sequence_ids = self.env['freight.sequence'].search([('company_id', '=', self.company_id.id), ('ir_model_id.model', '=', self._name)])
        if not freight_sequence_ids:
            return self
        if all(field_name in vals for field_name in field_name_lst):
            to_update_values = {}
            for ir_field in freight_sequence_ids.mapped('ir_field_id'):
                freight_sequences = freight_sequence_ids.filtered(lambda fs: fs.ir_field_id == ir_field)
                matched_sequence = freight_sequences._match_record(self)
                for freight_seq in matched_sequence:
                    to_update_values.update({freight_seq.ir_field_id.name: freight_seq.get_dynamic_model_sequence(self)})
            self.with_context(update_freight_sequence_dynamic=True).update(to_update_values)

    def copy_data(self, default=None):
        if default is None:
            default = {}
        default['gross_weight_unit'] = self.gross_weight_unit
        default['volume_unit'] = self.volume_unit
        default['net_weight_unit'] = self.net_weight_unit
        default['weight_volume_unit'] = self.weight_volume_unit
        default['state'] = 'draft'
        if not self.is_package_group and self.quote_container_line_ids:
            default['quote_container_line_ids'] = [(0, 0, container_line.copy_data()[0]) for container_line in self.quote_container_line_ids]
        if self.is_package_group and self.quote_cargo_line_ids:
            default['quote_cargo_line_ids'] = [(0, 0, cargo_line.copy_data()[0]) for cargo_line in self.quote_cargo_line_ids]
        default['quotation_line_ids'] = [(0, 0, service_line.copy_data()[0]) for service_line in self.quotation_line_ids]
        return super(ShipmentQuote, self).copy_data(default)

    def action_open_parent_shipment_quote(self):
        return {
            'name': _('Shipment Quote'),
            'type': 'ir.actions.act_window',
            'res_model': 'shipment.quote',
            'view_mode': 'form',
            'res_id': self.cancelled_quote_id.id
        }

    def ensure_quote_approval(self, action='send'):
        self.ensure_one()
        if not self.quotation_line_ids:
            raise ValidationError(_('Add at least one charge to %s quotation.') % (action))

        if self.quote_for == 'shipment' and not self.quote_container_line_ids and not self.quote_cargo_line_ids:
            raise ValidationError(_('Add at least one package to %s quotation.') % (action))

        total_cargo_lines = any(line.count <= 0 for line in self.quote_cargo_line_ids)
        total_container_lines = any(line.count <= 0 for line in self.quote_container_line_ids)
        if total_cargo_lines or total_container_lines:
            raise ValidationError(_('Pack count must be greater than zero to %s quotation.') % (action))

    def action_publish_quote(self):
        self.ensure_one()
        self.ensure_quote_approval(action='publish')
        self.write({'state': 'sent'})

    def action_option_publish_confirm_wizard(self):
        self.ensure_one()
        return {
            'name': 'Confirmation',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'wizard.publish.quote.confirmation',
            'target': 'new',
            'context': {'default_shipment_quote_id': self.id},
        }

    def action_quote_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        self.ensure_quote_approval()
        template_id = self._find_mail_template()
        ctx = {
            'default_model': self._name,
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_quote_as_sent': True,
        }
        return {
            'name': 'Quote: Mail Composer',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_quote_as_sent'):
            self.filtered(lambda o: o.state == 'draft').write({'state': 'sent'})
        return super(ShipmentQuote, self.with_context(mail_post_autofollow=self.env.context.get('mail_post_autofollow', True))).message_post(**kwargs)

    def _find_mail_template(self):
        self.ensure_one()
        template_id = self.env['ir.model.data']._xmlid_to_res_id('fm_quote.shipment_quote_email_template', raise_if_not_found=False)
        if self.state == 'accept':
            template_id = self.env['ir.model.data']._xmlid_to_res_id('fm_quote.shipment_quote_confirmation_email_template', raise_if_not_found=False)
        return template_id

    def get_access_action(self, access_uid=None):
        """ Instead of the classic form view, redirect to the online quote if it exists. """
        self.ensure_one()
        user = access_uid and self.env['res.users'].sudo().browse(access_uid) or self.env.user
        if not user.share:
            return super(ShipmentQuote, self).get_access_action(access_uid)
        return {
            'type': 'ir.actions.act_url',
            'url': self.get_portal_url(),
            'target': 'self',
            'res_id': self.id,
        }

    @api.model
    def _cron_shipment_quote_expiry_date(self):
        shipment_quote_ids = self.env['shipment.quote'].search(
            [('quote_expiry_date', '!=', False),
             ('quote_expiry_date', '<=', fields.Date.today()), ('state', 'in', ['draft', 'to_approve', 'approved', 'sent'])])
        shipment_quote_ids.write({'state': 'expire'})

    def get_portal_visibility_state(self):
        return ['sent', 'expire', 'cancel', 'accept', 'reject']

    def _compute_access_url(self):
        super(ShipmentQuote, self)._compute_access_url()
        for quote in self:
            quote.access_url = '/my/shipment_quote/%s' % (quote.id)

    def _get_portal_return_action(self):
        self.ensure_one()
        return self.env.ref('fm_quote.action_shipment_quote')

    def action_reject(self):
        self.ensure_one()
        self.write({
            'state': 'reject'
        })

    def action_accept(self):
        self.ensure_one()
        self.write({
            'state': 'accept'
        })

    def _send_order_confirmation_mail(self):
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        for quote in self:
            template_id = quote._find_mail_template()
            if template_id:
                quote.with_context(force_send=True).message_post_with_template(template_id, composition_mode='comment', email_layout_xmlid="mail.mail_notification_paynow")

    def preview_shipment_quote(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    def _send_quote_rejection_mail(self):
        self.ensure_one()
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        template_id = self.env.ref('fm_quote.shipment_quote_rejection_email_template')
        if template_id:
            self.with_context(force_send=self._context.get('force_send', True)).message_post_with_template(
                template_id.id, composition_mode='comment', email_layout_xmlid="mail.mail_notification_paynow",
            )

    @api.model
    def get_tradelane_data(self, domain=[], limit=None, offset=None, **kwargs):
        fields = ['port_of_loading_id', 'port_of_discharge_id:count']

        return tools.prepare_group(self, domain=domain, fields=fields, limit=limit, offset=offset, format_dict={
            'Tradelane': lambda x: x.get("port_of_loading_id") and x.get("port_of_discharge_id") and f'{x.get("port_of_loading_id")[1]} > {x.get("port_of_discharge_id")[1]}',
            'Count': '__count'
        }, **kwargs)

    @api.model
    def get_quote_by_status_data(self, domain=[], limit=10, offset=0, **kwargs):
        """ @returns [{
                'Status': String,
                'Count': Integer
            }]
        """
        self = self.with_context(**kwargs.get('context', {}))
        tableData = []
        # Converted
        converted_domain = domain + [('freight_shipment_count', '>', 0), ('state', '=', 'accept')]
        converted_count = self.search_count(converted_domain)
        tableData.append({
            'Status': 'Converted as Booking',
            'Count': converted_count,
            '__domain': converted_domain
        })

        # Lost
        lost_domain = domain + [('freight_shipment_count', '<=', 0), ('state', 'in', ['expire', 'reject'])]
        lost_count = self.search_count(lost_domain)
        tableData.append({
            'Status': 'Lost',
            'Count': lost_count,
            '__domain': lost_domain
        })

        # Pending
        pending_domain = domain + [('freight_shipment_count', '<=', 0), ('state', 'not in', ['expire', 'reject'])]
        pending_count = self.search_count(pending_domain)
        tableData.append({
            'Status': 'Pending',
            'Count': pending_count,
            '__domain': pending_domain
        })
        return tableData

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s' % self.name.replace('/', '_')

    def action_create_revised_quote(self):
        self.ensure_one()
        revised_quote_vals = self.copy_data(default={'cancelled_quote_id': self.id,
                                                     'transport_mode_id': self.transport_mode_id.id,
                                                     'shipment_type_id': self.shipment_type_id.id,
                                                     'cargo_type_id': self.cargo_type_id.id})
        revised_quote_id = self.env['shipment.quote'].create(revised_quote_vals)
        self.state = 'cancel'
        return {
            'name': 'Quotes',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shipment.quote',
            'res_id': revised_quote_id.id
        }

    @api.model
    def get_customer_data(self, domain=[], limit=None, offset=0, count=False, **kwargs):
        self = self.with_context(**kwargs.get('context', {}))
        tableData = []
        lines = self.read_group(domain, ['client_id'], ['client_id'], limit=limit, lazy=False)
        if count:
            return len(lines[offset: limit])

        key_dict = self.fields_get(['state'])['state']['selection']
        for line in lines:
            total = 0
            line_values = {'Customer': line['client_id'] and line['client_id'][1] or 'Not Available'}
            for key, value in key_dict:
                if key == 'draft':
                    continue
                line_values[value] = self.search_count(expression.AND([line['__domain'], [('state', '=', key)]]))
                total += line_values[value]

            line_values['Total'] = total
            tableData.append(line_values)

        tableData.sort(key=lambda x: x['Accepted'], reverse=True)
        return tableData[offset: limit]

    @api.onchange('is_courier_shipment')
    def _onchange_is_courier_shipment(self):
        if not self._origin and self.is_courier_shipment:
            self.shipment_type_id = False
            self.transport_mode_id = False

    @api.constrains('is_courier_shipment', 'cargo_type_id', 'shipment_type_id')
    def check_is_courier_shipment(self):
        for rec in self:
            if rec.is_courier_shipment:
                if rec.cargo_type_id and not rec.cargo_type_id.is_courier_shipment:
                    raise ValidationError(_("You can't use %s cargo type with courier shipment.") % (rec.cargo_type_id.name))

    @api.onchange('client_id')
    def _onchange_client_id_field(self):
        if not self.opportunity_id:
            self.user_id = self.client_id.user_id.id or self.env.user.id

    def unlink(self):
        for quote in self:
            if quote.freight_shipment_ids:
                raise ValidationError(_("You can't delete Quotation once shipment is created."))
            if quote.state != 'draft':
                raise ValidationError(_("Only Draft Quotation are allowed to delete."))
        return super().unlink()
