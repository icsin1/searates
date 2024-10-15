from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightMasterShipmentPackageMixin(models.Model):
    _name = 'freight.master.shipment.package'
    _inherit = ['freight.shipment.package.mixin']
    _description = 'Master Shipment Package'

    shipment_id = fields.Many2one('freight.master.shipment', required=True, ondelete='cascade')
    transport_mode_id = fields.Many2one(related='shipment_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    company_id = fields.Many2one('res.company', related='shipment_id.company_id', store=True)
    house_shipment_id = fields.Many2one('freight.house.shipment', string="House Shipment",
                                        related='house_shipment_pack_id.shipment_id', store=True)

    allow_container_number_ids = fields.Many2many('freight.master.shipment.container.number',
                                                  compute='_compute_allow_container_number')
    package_item_ids = fields.One2many('freight.house.shipment.package.item', 'shipment_package_id',
                                       string='Package Item')

    house_shipment_pack_id = fields.Many2one('freight.house.shipment.package', copy=False, ondelete='cascade')

    package_mode = fields.Selection(related='house_shipment_pack_id.package_mode', store=True, readonly=False)

    # Package if package_mode = Package
    package_type_id = fields.Many2one(
        'uom.uom', string='Package Type',
        related='house_shipment_pack_id.package_type_id', store=True, readonly=False,
        domain=lambda self: "['|', ('transport_mode_ids', '=', transport_mode_id), ('transport_mode_ids', '=', False), ('category_id', '=', %s)]" % self.env.ref(
            'freight_base.product_uom_categ_pack').id)
    container_type_id = fields.Many2one(related='house_shipment_pack_id.container_type_id', store=True,
                                        readonly=False)  # Required if packaging_mode = Container

    quantity = fields.Integer(related='house_shipment_pack_id.quantity', store=True, readonly=False)
    pack_count = fields.Integer(compute="_compute_pack_count", string="Pack Count", store=True, readonly=False)

    container_number = fields.Many2one(related='house_shipment_pack_id.container_number', store=True, readonly=False)
    seal_number = fields.Char(related='house_shipment_pack_id.seal_number', store=False, readonly=False)
    customs_seal_number = fields.Char(related='house_shipment_pack_id.customs_seal_number', store=False, readonly=False)
    description = fields.Text(related='house_shipment_pack_id.description', store=True, readonly=False)
    hbl_description = fields.Text(related='house_shipment_pack_id.hbl_description', store=True, readonly=False)

    length = fields.Float(related='house_shipment_pack_id.length', store=True, readonly=False)
    width = fields.Float(related='house_shipment_pack_id.width', store=True, readonly=False)
    height = fields.Float(related='house_shipment_pack_id.height', store=True, readonly=False)
    dimension_uom_id = fields.Many2one(related='house_shipment_pack_id.dimension_uom_id', store=True, readonly=False)

    weight_unit = fields.Float(related='house_shipment_pack_id.weight_unit', store=True, readonly=False)
    weight_unit_uom_id = fields.Many2one(related='house_shipment_pack_id.weight_unit_uom_id', store=True, readonly=False)

    volume_unit = fields.Float(related='house_shipment_pack_id.volume_unit', store=True, readonly=False)
    volume_unit_uom_id = fields.Many2one(related='house_shipment_pack_id.volume_unit_uom_id', readonly=False, store=True)

    volumetric_weight = fields.Float(related='house_shipment_pack_id.volumetric_weight', store=True, readonly=False)
    weight_volume_unit_uom_id = fields.Many2one(
        related='house_shipment_pack_id.weight_volume_unit_uom_id', store=True, readonly=False,
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])

    is_hazardous = fields.Boolean(related='house_shipment_pack_id.is_hazardous', store=True, readonly=False)
    haz_class_id = fields.Many2one(related='house_shipment_pack_id.haz_class_id', store=True, readonly=False)
    un_code = fields.Char(related='house_shipment_pack_id.un_code', store=True, readonly=False)

    haz_sub_class_id = fields.Many2one(related='house_shipment_pack_id.haz_sub_class_id', store=True, readonly=False, domain="[('haz_class_id', '=', haz_class_id)]")
    package_group = fields.Selection(related='house_shipment_pack_id.package_group', store=True, readonly=False, string="Package Group Type")
    package_info = fields.Many2one(related='house_shipment_pack_id.package_info', store=True, readonly=False, string='Package Info')
    marine_pollutant = fields.Selection(related='house_shipment_pack_id.marine_pollutant', store=True, readonly=False, string="Marine Pollutant")
    flash_point = fields.Float(string='Flash point', related='house_shipment_pack_id.flash_point', store=True, readonly=False)
    ems_number = fields.Char(string='EMS Number', related='house_shipment_pack_id.ems_number', store=True, readonly=False)
    emergency_remark = fields.Char(string='Emergency Remark', related='house_shipment_pack_id.emergency_remark', store=True, readonly=False)

    marksnnums = fields.Char(related='house_shipment_pack_id.marksnnums', store=True, readonly=False)
    mode_type = fields.Selection(related="shipment_id.mode_type", store=True)

    # Add packages/commodities from house
    master_package_group_ids = fields.One2many('freight.master.shipment.package', 'master_container_package_id',
                                               string='Package Groups')
    master_container_package_id = fields.Many2one('freight.master.shipment.package', ondelete='cascade')
    master_commodity_ids = fields.One2many('freight.master.package.commodity', 'master_package_group_id',
                                           string='Commodities')

    # FLC/LCL package and commodity auto calculate based on weight,volume & Volumetric weight
    total_master_weight_unit = fields.Float(compute='_compute_total_master_weight_volume_data', store=True,
                                            string="Weight ")
    total_master_volume_unit = fields.Float(compute='_compute_total_master_weight_volume_data', store=True,
                                            string="Volume ")
    total_master_volumetric_weight = fields.Float(compute='_compute_total_master_weight_volume_data', store=True,
                                                  string="Volumetric Weight ")

    container_master_weight_uom_id = fields.Many2one('uom.uom', string='Weight UoM ', compute='_compute_master_packages_weight_uom', store=True)
    container_master_volume_uom_id = fields.Many2one('uom.uom', string='Volume UoM ', compute='_compute_master_packages_volume_uom', store=True)
    container_master_volumetric_weight_uom_id = fields.Many2one('uom.uom', string='Volumetric UoM', compute='_compute_master_volumetric_weight_uom', store=True)
    master_sr_no = fields.Integer(related='house_shipment_pack_id.sr_no', string='Sr#')

    container_package_types = fields.Text(string='Package Types', compute='_compute_container_package_types', store=True)
    commodity_types = fields.Text(string='Commodity Types', compute='_compute_container_package_types', store=True)
    is_part_bl = fields.Boolean(related='house_shipment_pack_id.is_part_bl')

    # Net Weight
    net_weight = fields.Float(related='house_shipment_pack_id.net_weight', store=True, readonly=False)
    net_weight_unit_uom_id = fields.Many2one(
        related='house_shipment_pack_id.net_weight_unit_uom_id', store=True, readonly=False,
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])
    total_master_net_weight = fields.Float(compute='_compute_total_master_weight_volume_data', store=True, string="Net Weight ")
    container_master_net_weight_uom_id = fields.Many2one('uom.uom', compute='_compute_master_net_weight_uom', store=True)
    is_oog_container = fields.Boolean(related='container_type_id.category_id.is_oog_container', store=True)

    over_lenght = fields.Float(related='house_shipment_pack_id.over_lenght', store=True, readonly=False)
    over_lenght_uom_id = fields.Many2one(related='house_shipment_pack_id.over_lenght_uom_id', store=True,
                                         readonly=False)
    over_height = fields.Float(related='house_shipment_pack_id.over_height', store=True, readonly=False)
    over_height_uom_id = fields.Many2one(related='house_shipment_pack_id.over_height_uom_id', store=True,
                                         readonly=False)
    over_width = fields.Float(related='house_shipment_pack_id.over_width', store=True, readonly=False)
    over_width_uom_id = fields.Many2one(related='house_shipment_pack_id.over_width_uom_id', store=True, readonly=False)
    is_req_loading_handling = fields.Selection(related='house_shipment_pack_id.is_req_loading_handling', store=True,
                                               readonly=False)
    is_under_deck_requested = fields.Boolean(related='house_shipment_pack_id.is_under_deck_requested', store=True,
                                             readonly=False)

    stuffing_date = fields.Date('Stuffing Date', related='house_shipment_pack_id.stuffing_date', readonly=False)
    stuffing_cfs_id = fields.Many2one("freight.un.location", string="CFS",
                                      related='house_shipment_pack_id.stuffing_cfs_id', readonly=False)
    stuffing_confirmed = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Confirmed",
                                          related='house_shipment_pack_id.stuffing_confirmed', readonly=False)
    destuffing_date = fields.Date('DeStuffing Date', related='house_shipment_pack_id.destuffing_date', readonly=False)
    destuffing_cfs_id = fields.Many2one("freight.un.location", string="CFS",
                                        related='house_shipment_pack_id.destuffing_cfs_id', readonly=False)
    destuffing_confirmed = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Confirmed",
                                            related='house_shipment_pack_id.destuffing_confirmed', readonly=False)

    @api.depends('shipment_id', 'container_type_id')
    def _compute_allow_container_number(self):
        for rec in self:
            containers = rec.shipment_id.carrier_booking_container_ids
            if rec.package_mode == 'container':
                containers = containers.filtered_domain([('container_type_id', '=', rec.container_type_id.id)])
            rec.allow_container_number_ids = [(6, False, containers.container_number_ids.ids)]

    def action_unlink_shipment(self):
        self.write({'container_number': False})
        self.house_shipment_pack_id.write({'container_number': False})
        self._onchange_container_number()

    @api.depends('master_package_group_ids', 'master_commodity_ids',
                 'master_package_group_ids.weight_unit_uom_id', 'master_package_group_ids.weight_unit',
                 'master_package_group_ids.volume_unit_uom_id', 'master_package_group_ids.volume_unit',
                 'master_package_group_ids.weight_volume_unit_uom_id', 'master_package_group_ids.volumetric_weight',
                 'master_commodity_ids.weight_uom_id', 'master_commodity_ids.gross_weight',
                 'master_commodity_ids.volume_uom_id', 'master_commodity_ids.volume',
                 'master_commodity_ids.volumetric_weight_uom_id', 'master_commodity_ids.volumetric_weight',
                 'house_shipment_pack_id.total_weight_unit',
                 'house_shipment_pack_id.total_volume_unit', 'house_shipment_pack_id.total_volumetric_weight',
                 'container_master_weight_uom_id', 'container_master_volume_uom_id', 'container_master_volumetric_weight_uom_id',
                 'master_package_group_ids.net_weight', 'master_package_group_ids.net_weight_unit_uom_id',
                 'master_commodity_ids.net_weight', 'master_commodity_ids.net_weight_unit_uom_id')
    def _compute_total_master_weight_volume_data(self):
        for rec in self:
            rec.total_master_weight_unit = 0
            rec.total_master_volume_unit = 0
            rec.total_master_volumetric_weight = 0
            rec.total_master_net_weight = 0
            if rec.package_mode == 'container':
                rec.total_master_weight_unit = sum(
                    [pack.weight_unit_uom_id._compute_quantity(pack.weight_unit, rec.container_master_weight_uom_id) for pack in
                     rec.master_package_group_ids])
                rec.total_master_volume_unit = sum(
                    [pack.volume_unit_uom_id._compute_quantity(pack.volume_unit, rec.container_master_volume_uom_id) for pack in
                     rec.master_package_group_ids])
                rec.total_master_volumetric_weight = sum(
                    [pack.weight_volume_unit_uom_id._compute_quantity(pack.volumetric_weight,
                                                                      rec.container_master_volumetric_weight_uom_id)
                     for pack in rec.master_package_group_ids])
                rec.total_master_net_weight = sum(
                    [pack.net_weight_unit_uom_id._compute_quantity(pack.net_weight,
                                                                   rec.container_master_net_weight_uom_id)
                     for pack in rec.master_package_group_ids])
            else:
                rec.total_master_weight_unit = sum(
                    [comm.weight_uom_id._compute_quantity(comm.gross_weight, rec.container_master_weight_uom_id) for comm in
                     rec.master_commodity_ids])
                rec.total_master_volume_unit = sum(
                    [comm.volume_uom_id._compute_quantity(comm.volume, rec.container_master_volume_uom_id) for comm in
                     rec.master_commodity_ids])
                rec.total_master_volumetric_weight = sum(
                    [comm.volumetric_weight_uom_id._compute_quantity(comm.volumetric_weight,
                                                                     rec.container_master_volumetric_weight_uom_id)
                     for comm in rec.master_commodity_ids])
                rec.total_master_net_weight = sum(
                    [comm.net_weight_unit_uom_id._compute_quantity(comm.net_weight,
                                                                   rec.container_master_net_weight_uom_id)
                     for comm in rec.master_commodity_ids])

    @api.onchange('weight_unit_uom_id')
    def _onchange_weight_unit_uom_id(self):
        if (self.master_container_package_id and self.package_mode == 'package' and
                self.master_container_package_id.container_master_weight_uom_id):
            if (self.weight_unit_uom_id and
                    self.weight_unit_uom_id.id != self.master_container_package_id.container_master_weight_uom_id.id):
                self.weight_unit_uom_id = False
                return self.raise_warning_for_uom('Weight',
                                                  self.master_container_package_id.container_master_weight_uom_id.name)

    @api.onchange('volume_unit_uom_id')
    def _onchange_volume_unit_uom_id(self):
        if (self.master_container_package_id and self.package_mode == 'package' and
                self.master_container_package_id.container_master_volume_uom_id):
            if (self.volume_unit_uom_id and
                    self.volume_unit_uom_id.id != self.master_container_package_id.container_master_volume_uom_id.id):
                self.volume_unit_uom_id = False
                return self.raise_warning_for_uom('Volume',
                                                  self.master_container_package_id.container_master_volume_uom_id.name)

    @api.onchange('weight_volume_unit_uom_id')
    def _onchange_volumetric_weight_uom_id(self):
        if (self.master_container_package_id and self.package_mode == 'package' and
                self.master_container_package_id.container_master_volumetric_weight_uom_id):
            if (self.weight_volume_unit_uom_id and
                    self.weight_volume_unit_uom_id.id != self.master_container_package_id.container_master_volumetric_weight_uom_id.id):
                self.weight_volume_unit_uom_id = False
                return self.raise_warning_for_uom('Volumetric weight',
                                                  self.master_container_package_id.container_master_volumetric_weight_uom_id.name)

    def raise_warning_for_uom(self, uom_name, package_main_uom):
        warning = {
            'title': _("Warning"),
            'message': _('%s uom should be same for all commodity to %s.' % (uom_name, package_main_uom))
        }
        return {'warning': warning}

    def action_save(self):
        pass

    def action_open_from_view(self):
        self.ensure_one()
        form_view_id = self.env.ref('freight_management.view_freight_master_shipment_package_form_wizard').id
        return {
            'name': "Package Group",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'res_model': self._name,
            'res_id': self.id,
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit', **self._context},
        }

    @api.depends('master_container_package_id', 'master_package_group_ids', 'master_commodity_ids', 'master_commodity_ids.weight_uom_id',
                 'master_package_group_ids.weight_unit_uom_id')
    def _compute_master_packages_weight_uom(self):
        for rec in self:
            weight_unit_uom_id = rec.company_id.weight_uom_id
            if not rec.master_container_package_id and rec.package_mode == 'container' and rec.master_package_group_ids:
                weight_unit_uom_id = rec.master_package_group_ids[0].weight_unit_uom_id
            if rec.master_commodity_ids:
                weight_unit_uom_id = rec.master_commodity_ids[0].weight_uom_id

            rec.container_master_weight_uom_id = weight_unit_uom_id.id if weight_unit_uom_id else False

    @api.depends('master_container_package_id', 'master_package_group_ids', 'master_commodity_ids', 'master_commodity_ids.volume_uom_id',
                 'master_package_group_ids.volume_unit_uom_id')
    def _compute_master_packages_volume_uom(self):
        for rec in self:
            volume_unit_uom_id = rec.company_id.volume_uom_id
            if not rec.master_container_package_id and rec.package_mode == 'container' and rec.master_package_group_ids:
                volume_unit_uom_id = rec.master_package_group_ids[0].volume_unit_uom_id
            if rec.master_commodity_ids:
                volume_unit_uom_id = rec.master_commodity_ids[0].volume_uom_id

            rec.container_master_volume_uom_id = volume_unit_uom_id.id if volume_unit_uom_id else False

    @api.depends('master_container_package_id', 'master_package_group_ids', 'master_commodity_ids', 'master_commodity_ids.volumetric_weight_uom_id',
                 'master_package_group_ids.weight_volume_unit_uom_id')
    def _compute_master_volumetric_weight_uom(self):
        for rec in self:
            volumetric_weight_unit_uom_id = rec.company_id.weight_uom_id
            if not rec.master_container_package_id and rec.package_mode == 'container' and rec.master_package_group_ids:
                volumetric_weight_unit_uom_id = rec.master_package_group_ids[0].weight_volume_unit_uom_id
            if rec.master_commodity_ids:
                volumetric_weight_unit_uom_id = rec.master_commodity_ids[0].volumetric_weight_uom_id

            rec.container_master_volumetric_weight_uom_id = volumetric_weight_unit_uom_id.id if volumetric_weight_unit_uom_id else False

    @api.depends('house_shipment_pack_id.package_group_ids.quantity', 'quantity', 'master_package_group_ids')
    def _compute_pack_count(self):
        for rec in self:
            rec.pack_count = sum(rec.master_package_group_ids.mapped('quantity'))

    @api.onchange('pack_count')
    def check_pack_count(self):
        for rec in self:
            if rec.pack_count < 0:
                raise ValidationError('Pack count should not be negative.')

    @api.depends('master_package_group_ids', 'master_commodity_ids', 'house_shipment_pack_id.package_group_ids',
                 'master_commodity_ids.pack_uom_id')
    def _compute_container_package_types(self):
        for master_ship_pack in self:
            packages = []
            commodities = []
            # For FCL
            packages = master_ship_pack.mapped('master_package_group_ids.package_type_id.name')
            # For LCL
            commodities = master_ship_pack.mapped('master_commodity_ids.pack_uom_id.name')
            master_ship_pack.container_package_types = ', '.join(list(filter(None, packages)))
            master_ship_pack.commodity_types = ', '.join(list(filter(None, commodities)))

    @api.depends('master_container_package_id', 'master_package_group_ids', 'master_commodity_ids',
                 'master_package_group_ids.net_weight_unit_uom_id', 'master_commodity_ids.net_weight_unit_uom_id')
    def _compute_master_net_weight_uom(self):
        for rec in self:
            net_weight_unit_uom_id = rec.company_id.weight_uom_id
            if not rec.master_container_package_id and rec.package_mode == 'container' and rec.master_package_group_ids:
                net_weight_unit_uom_id = rec.master_package_group_ids[0].net_weight_unit_uom_id
            if rec.master_commodity_ids:
                net_weight_unit_uom_id = rec.master_commodity_ids[0].net_weight_unit_uom_id

            rec.container_master_net_weight_uom_id = net_weight_unit_uom_id.id if net_weight_unit_uom_id else False

    @api.onchange('net_weight_unit_uom_id')
    def _onchange_net_weight_unit_uom_id(self):
        if (self.master_container_package_id and self.package_mode == 'package' and
                self.master_container_package_id.container_master_net_weight_uom_id):
            if (self.net_weight_unit_uom_id and
                    self.net_weight_unit_uom_id.id != self.master_container_package_id.container_master_net_weight_uom_id.id):
                self.net_weight_unit_uom_id = False
                return self.raise_warning_for_uom('Weight',
                                                  self.master_container_package_id.container_master_net_weight_uom_id.name)


class FreightMasterShipmentPackageItem(models.Model):
    _name = 'freight.master.shipment.package.item'
    _inherit = ['freight.shipment.package.item.mixin']
    _description = 'Master Shipment Package Item'

    shipment_package_id = fields.Many2one('freight.master.shipment.package', required=True, ondelete='cascade')
