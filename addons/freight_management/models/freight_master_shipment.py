import base64
from itertools import groupby

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError
import json

from lxml import etree

MASTER_STATE = [
    ('draft', 'Created'),
    ('booked', 'Ext.Booked'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
]
# FIXME: Once we are ready with stages to make shipment readonly
# READONLY_STAGE = {'draft': [('readonly', False)]}
READONLY_STAGE = {}


class FreightMasterShipment(models.Model):
    _name = 'freight.master.shipment'
    _description = 'Master Shipment'
    _inherit = ['freight.shipment.mixin']
    _rec_name = 'display_name'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):

        res = super(FreightMasterShipment, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                                 submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form' and not self.env.user.has_group('freight_management.group_super_admin'):
            for node in doc.xpath("//field"):
                if node.get("modifiers") is not None:
                    modifiers = json.loads(node.get("modifiers"))
                    if 'readonly' not in modifiers:
                        modifiers['readonly'] = [['state', 'in', ['cancelled', 'completed']]]
                    else:
                        if type(modifiers['readonly']) != bool:
                            modifiers['readonly'].insert(-1, '|')
                            modifiers['readonly'] += [['state', 'in', ['cancelled', 'completed']]]
                    node.set('modifiers', json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc)
        return res

    @api.depends('carrier_booking_container_ids.no_of_teu')
    def _compute_total_teu(self):
        for master in self:
            master.total_teu = sum(master.carrier_booking_container_ids.mapped('no_of_teu'))

    display_name = fields.Char(compute='_compute_display_name', store=True, copy=False)
    name = fields.Char(string='Shipment Number', store=True, readonly=True, copy=False, default='New')

    @api.depends('is_courier_shipment')
    def _compute_shipment_type_domain(self):
        for rec in self:
            domain = ['|', ('is_courier_shipment', '=', False), ('is_courier_shipment', '=', rec.is_courier_shipment)]
            rec.shipment_type_domain = json.dumps(domain)

    shipment_type_domain = fields.Char(compute='_compute_shipment_type_domain', store=True)

    container_number_list_file = fields.Binary()
    container_document_file_name = fields.Char()
    upload_file_message = fields.Text(copy=False)

    # House Shipments
    house_shipment_ids = fields.One2many('freight.house.shipment', 'parent_id', string='House Shipments')
    house_shipment_count = fields.Integer(compute='_compute_house_shipment_count', store=True)

    # Carrier booking documents and containers
    carrier_booking_document_ids = fields.One2many('freight.master.shipment.carrier.document', 'shipment_id',
                                                   string='Carrier Booking Documents')
    carrier_booking_container_ids = fields.One2many('freight.master.shipment.carrier.container', 'shipment_id',
                                                    string='Booking Containers')
    carrier_agent_id = fields.Many2one('res.partner', copy=False)
    total_teu = fields.Float(compute="_compute_total_teu", store=True, string="Total TEU")

    # Packages
    package_ids = fields.One2many('freight.master.shipment.package', 'shipment_id', string='Packages',
                                  domain=[('package_mode', '=', 'package')])
    container_ids = fields.One2many('freight.master.shipment.package', 'shipment_id', string='Containers',
                                    domain=[('package_mode', '=', 'container'),
                                            ('master_container_package_id', '=', False)])
    packages_count = fields.Integer(compute='_compute_packages', store=True)
    containers_count = fields.Integer(compute='_compute_packages', store=True)
    list_containers_count = fields.Integer(compute='_compute_list_container_count')

    # routes
    route_ids = fields.One2many('freight.master.shipment.route', 'shipment_id', string='Routes')

    # Events
    event_ids = fields.One2many('freight.master.shipment.event', 'shipment_id', string='Milestones Tracking')

    # Documents
    document_ids = fields.One2many('freight.master.shipment.document', 'shipment_id', string='Documents')
    document_count = fields.Integer(compute='_compute_document_count')

    state = fields.Selection(MASTER_STATE, default='draft', tracking=True, group_expand='_expand_states')
    air_state = fields.Selection(related='state', string='Air-Freight State')
    container_number_ids = fields.One2many('freight.master.shipment.container.number', 'shipment_id',
                                           string='Container Numbers')

    # Terms and Conditions
    terms_ids = fields.One2many('freight.master.shipment.terms', 'shipment_id', string='Terms & Conditions')

    tag_ids = fields.Many2many('freight.shipment.tag', 'freight_master_shipment_tag_rel', 'shipment_id', 'tag_id',
                               copy=False, string="Tags")

    # Readonly Abstract model column for master shipment
    company_id = fields.Many2one(states=READONLY_STAGE)
    shipment_date = fields.Date(states=READONLY_STAGE, default=lambda self: fields.Date.today())
    origin_un_location_id = fields.Many2one(states=READONLY_STAGE)
    destination_un_location_id = fields.Many2one(states=READONLY_STAGE)
    origin_port_un_location_id = fields.Many2one(states=READONLY_STAGE, string='Origin Port/Airport')
    destination_port_un_location_id = fields.Many2one(states=READONLY_STAGE, string='Destination Port/Airport')
    shipment_partner_ids = fields.One2many('freight.master.shipment.partner', 'freight_shipment_id', string='Parties', states=READONLY_STAGE)
    latest_milestone_id = fields.Many2one('freight.event.type', string="Latest Milestone",
                                          compute='_compute_latest_milestone', store=True)

    # AMS Number
    ams_number = fields.Text('AMS Number')
    enable_disable_shipping_line = fields.Boolean(string="Enable SCAC Code",
                                                  related='company_id.enable_disable_shipping_line', store=True)
    master_check = fields.Boolean('Master Check', compute='_compute_master_check')
    consolidation_type_id = fields.Many2one('consolidation.type', string='Consolidation Type')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'The Master Shipment Number must be unique per Shipment!'),
        ('carrier_booking_reference_number_unique', 'CHECK(1=1)', "IGNORE")
    ]

    @api.depends('company_id')
    def _compute_master_check(self):
        is_master_check = self.env['ir.config_parameter'].sudo().get_param('freight_management.enable_non_mandatory_fields')
        for rec in self:
            if is_master_check:
                rec.master_check = True
            else:
                rec.master_check = False

    @api.depends('event_ids')
    def _compute_latest_milestone(self):
        for record in self:
            for milestone in record.event_ids:
                record.latest_milestone_id = milestone.event_type_id.id

    @api.constrains('shipment_partner_ids')
    def _check_shipment_partner_ids(self):
        is_party_type = self.env['ir.config_parameter'].sudo().get_param('freight_management.party_types')
        for shipment in self:
            existing_parties = []
            for party in shipment.shipment_partner_ids.filtered(
                    lambda p: (p.partner_type_id.code, 'in', ['destination_agent', 'shipper', 'consignee'])):
                if party.partner_type_id.id in existing_parties and is_party_type:
                    raise UserError(_('Duplication of party type cannot be allowed.'))
                if party.partner_type_id.id in existing_parties and not is_party_type:
                    raise UserError(_('Duplication of non vendor party type cannot be Allowed.'))

                existing_parties.append(party.partner_type_id.id)

    @api.depends('carrier_booking_reference_number', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.carrier_booking_reference_number or rec.name

    def _expand_states(self, states, domain, order):
        return [key for key, dummy in type(self).state.selection]

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if not self.shipment_type_id or not self.cargo_type_id or not self.transport_mode_id:
            raise UserError(
                _("User Could Not Duplicate The Master Shipment with out Transport Mode, Shipment Type and Cargo Type."))
        record = super().copy(default)
        if record.shipment_type_id:
            record.shipment_type_id = False
        if record.cargo_type_id:
            record.cargo_type_id = False
        if record.transport_mode_id:
            record.transport_mode_id = False
        return record

    @api.onchange('shipping_line_id')
    def _onchange_shipping_line_id(self):
        self.carrier_agent_id = False

    @api.onchange('shipping_line_id', 'enable_disable_shipping_line', 'transport_mode_id')
    def _onchange_shipping_line(self):
        if self.transport_mode_id.mode_type == 'sea' and self.enable_disable_shipping_line:
            if self.shipping_line_id:
                self.carrier_booking_reference_number = self.shipping_line_id.scac_code
            else:
                self.carrier_booking_reference_number = False
        else:
            self.carrier_booking_reference_number = False

    @api.constrains('carrier_booking_reference_number', 'state')
    def _check_unique_carrier_booking_reference_number(self):
        for master in self:
            name = 'MBL'
            if master.mode_type == 'air':
                name = 'MAWB'
            elif master.mode_type == 'land':
                name = 'MLR'
            if master.carrier_booking_reference_number:
                domain = [('carrier_booking_reference_number', '=ilike', master.carrier_booking_reference_number),
                          ('company_id', '=', master.company_id.id), ('state', '!=', 'cancelled')]
                if self.search_count(domain) > 1:
                    raise ValidationError(_('%s Number must be unique!') % (name))
            else:
                if master.state not in ['draft', 'cancelled']:
                    raise ValidationError(_('%s Number is required.') % (name))

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        # Direct House Shipment to Direct Master Shipment
        if self._name == 'freight.master.shipment' and self.is_direct_shipment and self.house_shipment_ids:
            values = {}
            house_shipment = self.house_shipment_ids[0]
            fields_lst = ['cargo_type_id', 'origin_port_un_location_id', 'destination_port_un_location_id',
                          'shipping_line_id']
            if house_shipment.transport_mode_id.id != self.transport_mode_id.id or not house_shipment:
                values = {field: False for field in fields_lst}
                self.update(values)
            else:
                values = {field: house_shipment[field] for field in fields_lst}
                values.update({
                    'origin_port_un_location_id': house_shipment.origin_port_un_location_id.id,
                    'destination_port_un_location_id': house_shipment.destination_port_un_location_id.id,
                })
                self.update(values)
        else:
            super()._onchange_transport_mode_id()

    @api.depends('container_ids', 'package_ids', 'package_ids.quantity')
    def _compute_packages(self):
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

    @api.depends(
        'auto_update_weight_volume',
        'cargo_is_package_group',
        'container_ids',
        'container_ids.weight_unit',
        'container_ids.weight_unit_uom_id',
        'container_ids.volume_unit',
        'container_ids.volume_unit_uom_id',
        'container_ids.volumetric_weight',
        'container_ids.total_master_net_weight',
        'package_ids',
        'package_ids.pack_count',
        'package_ids.weight_unit',
        'package_ids.weight_unit_uom_id',
        'package_ids.volume_unit',
        'package_ids.volume_unit_uom_id',
        'package_ids.volumetric_weight',
        'package_ids.total_master_net_weight'
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
                total_gross_weight = sum([p.container_master_weight_uom_id._compute_quantity(p.total_master_weight_unit, weight_uom) for p in shipment.package_ids])
                total_volumetric_weight_unit = sum([p.container_master_volumetric_weight_uom_id._compute_quantity(p.total_master_volumetric_weight, weight_uom) for p in shipment.package_ids])
                total_volume_unit = sum([p.container_master_volume_uom_id._compute_quantity(p.total_master_volume_unit, volume_uom) for p in shipment.package_ids])
                total_net_weight_unit = sum([p.container_master_net_weight_uom_id._compute_quantity(p.total_master_net_weight, weight_uom) for p in shipment.package_ids])
                pack_unit = sum(shipment.package_ids.mapped('quantity'))
                package_uom = shipment.package_ids.mapped('package_type_id') if len(shipment.package_ids.mapped('package_type_id')) == 1 else package_uom
            else:
                total_gross_weight = sum([c.container_master_weight_uom_id._compute_quantity(c.total_master_weight_unit, weight_uom) for c in shipment.container_ids])
                total_volumetric_weight_unit = sum([c.container_master_volumetric_weight_uom_id._compute_quantity(c.total_master_volumetric_weight, weight_uom) for c in shipment.container_ids])
                total_volume_unit = sum([c.container_master_volume_uom_id._compute_quantity(c.total_master_volume_unit, volume_uom) for c in shipment.container_ids])
                total_net_weight_unit = sum([c.container_master_net_weight_uom_id._compute_quantity(c.total_master_net_weight, weight_uom) for c in shipment.container_ids])
                pack_unit = sum(shipment.container_ids.mapped('pack_count'))
                package_uom_list = []
                for line in shipment.container_ids:
                    for package in line.master_package_group_ids:
                        package_uom_list.append(package.package_type_id)
                package_uom = package_uom_list[0] if len(set(package_uom_list)) == 1 else package_uom

            shipment.gross_weight_unit, shipment.gross_weight_unit_uom_id = (round(total_gross_weight or shipment.gross_weight_unit, 3),
                                                                             (weight_uom.id or shipment.gross_weight_unit_uom_id and shipment.gross_weight_unit_uom_id.id))
            shipment.weight_volume_unit, shipment.weight_volume_unit_uom_id = (round(total_volumetric_weight_unit or shipment.weight_volume_unit, 3),
                                                                               (weight_uom.id or shipment.weight_volume_unit_uom_id and shipment.weight_volume_unit_uom_id.id))
            shipment.volume_unit, shipment.volume_unit_uom_id = (round(total_volume_unit or shipment.volume_unit, 3),
                                                                 (volume_uom.id or shipment.volume_unit_uom_id and shipment.volume_unit_uom_id.id))
            shipment.net_weight_unit, shipment.net_weight_unit_uom_id = (round(total_net_weight_unit or shipment.net_weight_unit, 3),
                                                                         (weight_uom.id or shipment.net_weight_unit_uom_id and shipment.net_weight_unit_uom_id.id))
            shipment.pack_unit, shipment.pack_unit_uom_id = (round(pack_unit or shipment.pack_unit, 3),
                                                             (package_uom.id or shipment.pack_unit_uom_id and shipment.pack_unit_uom_id.id))

    @api.depends("house_shipment_ids")
    def _compute_house_shipment_count(self):
        for rec in self:
            rec.house_shipment_count = len(rec.house_shipment_ids)

    def _update_state_to_ext_booked(self):
        for shipment in self:
            if shipment.state == "draft" and shipment.carrier_booking_container_ids:
                shipment.state = "booked"

    @api.model_create_single
    def create(self, values):
        rec = super().create(values)
        rec._update_documents_list()
        if values.get('carrier_booking_container_ids'):
            rec._update_state_to_ext_booked()
        return rec

    def write(self, values):
        res = super().write(values)
        if values.get('carrier_booking_container_ids'):
            self._update_state_to_ext_booked()
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
            'res_model': 'freight.master.shipment.document',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('shipment_id', 'in', self.ids)],
            'context': {'default_shipment_id': self.id, 'search_default_group_by_mode': 1},
            'target': 'current',
        }

    def action_remove_all_packages(self):
        self.ensure_one()
        for commodity in self.package_ids.mapped('master_commodity_ids'):
            commodity.house_shipment_commodity_id.master_shipment_comm_id = False
        self.package_ids.master_commodity_ids.unlink()
        self.package_ids.unlink()
        self.container_ids.package_item_ids.unlink()
        self.container_ids.unlink()

    def action_change_status(self):
        self.ensure_one()
        default_context = {'default_shipment_id': self.id, 'default_state': self.state}
        return {
            'name': 'Change Status',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.master.shipment.status',
            'context': default_context
        }

    def prepare_commodity_vals(self, commodity):
        return {
            'commodity_id': commodity.commodity_id.id,
            'pieces': commodity.pieces,
            'pack_uom_id': commodity.pack_uom_id.id,
            'gross_weight': commodity.gross_weight,
            'weight_uom_id': commodity.weight_uom_id.id,
            'volume': commodity.volume,
            'volume_uom_id': commodity.volume_uom_id.id,
            'dimension_uom_id': commodity.dimension_uom_id.id,
            'volumetric_weight': commodity.volumetric_weight,
            'house_shipment_commodity_id': commodity.id
        }

    def prepare_package_vals(self, package):
        self.ensure_one()
        return {
            'shipment_id': self.id,
            'package_mode': 'package',
            'package_type_id': package.package_type_id.id,
            'house_shipment_pack_id': package.id,
            'quantity': package.quantity,
            'weight_unit': package.weight_unit,
            'volume_unit': package.volume_unit,
            'volumetric_weight': package.volumetric_weight,
            'weight_unit_uom_id': package.weight_unit_uom_id.id,
            'volume_unit_uom_id': package.volume_unit_uom_id.id,
            'weight_volume_unit_uom_id': package.weight_volume_unit_uom_id.id,
        }

    def action_fetch_packages_from_house_shipment(self):
        self.ensure_one()
        self.action_fetch_containers_from_house()
        PackageMixin = self.env['freight.shipment.package.mixin']
        MasterPackageObj = self.env['freight.master.shipment.package']
        MasterCommodityObj = self.env['freight.master.package.commodity']
        # As this function fetches package or containers from house to master shipment
        # so to ease the process we uses list of field names
        # and get value instead of writing a dictionary with static field name
        package_fields = list(PackageMixin._fields.keys())
        for house_shipment in self.house_shipment_ids:
            # LCL
            if house_shipment.packaging_mode == 'package':
                # Update/Fetch already linked package details
                for package in house_shipment.package_ids.filtered(lambda c: c.master_shipment_pack_id):
                    for commodity in package.commodity_ids.filtered(lambda a: not a.master_shipment_comm_id):
                        commodity_vals = self.prepare_commodity_vals(commodity)
                        commodity_vals.update({
                            'master_package_group_id': package.master_shipment_pack_id.id,
                        })
                        new_commodity = MasterCommodityObj.create(commodity_vals)
                        commodity.master_shipment_comm_id = new_commodity.id
                # Add not fetched/linked package details
                for package in house_shipment.package_ids.filtered(lambda c: not c.master_shipment_pack_id):
                    vals = {}
                    # prepare vals
                    for field in package_fields:
                        if isinstance(package[field], models.Model):
                            val = package[field].ids if field.endswith('_ids') else package[field].id
                        else:
                            val = package[field]
                        vals.update({field: val})
                    commodity_vals = []
                    for commodity in package.commodity_ids.filtered(lambda a: not a.master_shipment_comm_id):
                        commodity_vals.append((0, 0, self.prepare_commodity_vals(commodity)))
                    vals.update(
                        {'shipment_id': self.id, 'house_shipment_pack_id': package.id, 'package_mode': 'package',
                         'weight_unit': package.total_weight_unit, 'volume_unit': package.total_volume_unit,
                         'volumetric_weight': package.total_volumetric_weight,
                         'weight_unit_uom_id': package.container_weight_unit_uom_id.id,
                         'volume_unit_uom_id': package.container_volume_unit_uom_id.id,
                         'weight_volume_unit_uom_id': package.container_volumetric_weight_unit_uom_id.id,
                         'master_commodity_ids': commodity_vals})

                    new_pack = MasterPackageObj.create(vals)
                    package.master_shipment_pack_id = new_pack.id
                    for house_comm in package.commodity_ids:
                        for new_comm in new_pack.master_commodity_ids:
                            house_comm.master_shipment_comm_id = new_comm.id

            # FCL
            if house_shipment.packaging_mode == 'container':
                # Update already linked container from house shipment
                for container in house_shipment.container_ids.filtered(lambda c: c.master_shipment_pack_id):
                    vals = {}
                    # Prepare vals
                    for field in package_fields:
                        val = container[field]
                        # As we are preparing values dynamically we need to check whether
                        # the field is M2O then set id only
                        # and if the field is O2M or M2M then set ids
                        if isinstance(val, models.Model):
                            if isinstance(PackageMixin._fields[field], fields.Many2one):
                                val = val.id
                            elif isinstance(PackageMixin._fields[field], (fields.Many2many, fields.One2many)):
                                val = val.ids
                        vals.update({field: val})

                    house_container_package = container.package_group_ids.filtered(lambda c: not c.master_shipment_pack_id)
                    for package in house_container_package:
                        package_vals = self.prepare_package_vals(package)
                        package_vals.update({'master_container_package_id': container.master_shipment_pack_id.id})
                        new_container = MasterPackageObj.create(package_vals)
                        container.master_shipment_pack_id = new_container.id
                # Add not fetched Container with Package
                for container in house_shipment.container_ids.filtered(lambda c: not c.master_shipment_pack_id):
                    vals = {}
                    # Prepare vals
                    for field in package_fields:
                        val = container[field]
                        # As we are preparing values dynamically we need to check whether
                        # the field is M2O then set id only
                        # and if the field is O2M or M2M then set ids
                        if isinstance(val, models.Model):
                            if isinstance(PackageMixin._fields[field], fields.Many2one):
                                val = val.id
                            elif isinstance(PackageMixin._fields[field], (fields.Many2many, fields.One2many)):
                                val = val.ids
                        vals.update({field: val})
                    package_vals = []
                    for package in container.package_group_ids:
                        package_vals.append((0, 0, {**self.prepare_package_vals(package), 'master_container_package_id': container.master_shipment_pack_id.id}))
                    vals.update(
                        {'shipment_id': self.id, 'house_shipment_pack_id': container.id, 'package_mode': 'container',
                         'weight_unit': container.total_weight_unit, 'volume_unit': container.total_volume_unit,
                         'volumetric_weight': container.total_volumetric_weight,
                         'weight_unit_uom_id': container.container_weight_unit_uom_id.id,
                         'volume_unit_uom_id': container.container_volume_unit_uom_id.id,
                         'weight_volume_unit_uom_id': container.container_volumetric_weight_unit_uom_id.id,
                         'master_package_group_ids': package_vals})
                    new_container = MasterPackageObj.create(vals)
                    container.master_shipment_pack_id = new_container.id
                    for package in container.package_group_ids:
                        package.master_shipment_pack_id = new_container.id

    def action_assign_container(self):
        self.ensure_one()
        if self.packaging_mode != 'container':
            return

        # Getting container number with no link of package
        container_numbers = self.carrier_booking_container_ids.container_number_ids.filtered(
            lambda c: not c.package_ids)
        # Getting packages with no container mapping
        containers = self.container_ids.filtered(lambda c: not c.container_number)

        assigned_number = []
        for container in containers:
            type_container_numbers = container_numbers.filtered(
                lambda c: c.container_type_id == container.container_type_id and c.id not in assigned_number
            )
            if type_container_numbers:
                to_assign = type_container_numbers[-1]
                container.write({'container_number': to_assign.id, 'seal_number': to_assign.seal_number})
                assigned_number.append(to_assign.id)

    def copy_data(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        default['gross_weight_unit'] = self.gross_weight_unit
        default['gross_weight_unit_uom_id'] = self.gross_weight_unit_uom_id.id
        default['volume_unit'] = self.volume_unit
        default['volume_unit_uom_id'] = self.volume_unit_uom_id.id
        default['weight_volume_unit'] = self.weight_volume_unit
        default['weight_volume_unit_uom_id'] = self.weight_volume_unit_uom_id.id
        return super(FreightMasterShipment, self).copy_data(default)

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

    def action_open_freight_house_shipment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("freight_management.freight_shipment_view_houses_action")
        context = safe_eval(action['context'])
        detach_house = True if not self.is_direct_shipment else False
        context.update({'detach': detach_house})
        action['context'] = context
        return action

    def merge_containers(self, container_vals_list):

        def groupby_function(d):
            return d['container_type_id'], d['weight_unit'], d['weight_unit_uom_id'], d['volume_unit'], d[
                'volume_unit_uom_id'], d['volumetric_weight'], d['is_hazardous'], d['un_code'],

        container_list = []
        for distinct_values, groupby_res in groupby(sorted(container_vals_list, key=groupby_function),
                                                    groupby_function):
            result = list(groupby_res)
            if len(result) == 1:
                container_list.append((0, 0, result[0]))
            else:
                container_number_ids = []
                for container in result:
                    container_number_ids += container.get('container_number_ids')
                result = result[0]
                result['container_number_ids'] = container_number_ids
                result['container_count'] = len(container_number_ids)
                container_list.append((0, 0, result))
        return container_list

    def action_fetch_containers_from_house(self):
        self.ensure_one()
        # self.action_fetch_packages_from_house_shipment()
        house_container_ids = self.house_shipment_ids.mapped('container_ids').filtered(
            lambda container: container.container_number)
        container_ids = self.carrier_booking_container_ids.filtered(lambda container: container.house_shipment_id)
        values = []
        for house_container in house_container_ids:
            vals = {
                'container_type_id': house_container.container_type_id.id,
                'container_count': house_container.quantity,
                'no_of_packs': house_container.pack_count,
                'no_of_teu': house_container.no_of_teu,
                'weight_unit': house_container.total_weight_unit,
                'weight_unit_uom_id': house_container.weight_unit_uom_id.id,
                'volume_unit': house_container.total_volume_unit,
                'volume_unit_uom_id': house_container.volume_unit_uom_id.id,
                'volumetric_weight': house_container.total_volumetric_weight,
                'over_lenght': house_container.over_lenght,
                'over_lenght_uom_id': house_container.over_lenght_uom_id.id,
                'over_height': house_container.over_height,
                'over_height_uom_id': house_container.over_height_uom_id.id,
                'over_width': house_container.over_width,
                'over_width_uom_id': house_container.over_width_uom_id.id,
                'is_hazardous': house_container.is_hazardous,
                'description': house_container.description,
                'un_code': house_container.un_code,
                'house_shipment_id': house_container.shipment_id.id,
                'container_number_ids': [(4, house_container.container_number.id)]

            }
            values.append(vals)
        container_list = [(3, container.id) for container in container_ids]
        container_list += self.merge_containers(values)
        if container_list:
            self.write({
                'carrier_booking_container_ids': container_list
            })


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    # Master & Child Shipments
    parent_id = fields.Many2one('freight.master.shipment', string='Master Shipment', ondelete='set null', copy=False,
                                tracking=True)
