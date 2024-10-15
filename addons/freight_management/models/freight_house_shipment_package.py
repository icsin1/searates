from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json


class FreightHouseShipmentPackage(models.Model):
    _name = 'freight.house.shipment.package'
    _inherit = ['freight.shipment.package.mixin']
    _description = 'House Shipment Package'

    shipment_id = fields.Many2one('freight.house.shipment', ondelete='cascade')
    transport_mode_id = fields.Many2one(related='shipment_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)

    company_id = fields.Many2one('res.company', related='shipment_id.company_id', store=True)

    allow_container_number_ids = fields.Many2many('freight.master.shipment.container.number',
                                                  compute='_compute_allow_container_number')

    # IF FCL, each package have package groups which is directly linked with container_package_id
    container_package_id = fields.Many2one('freight.house.shipment.package', ondelete='cascade')
    package_group_ids = fields.One2many('freight.house.shipment.package', 'container_package_id',
                                        string='Package Groups')
    pack_count = fields.Integer(compute="_compute_pack_count", string="Pack Count", store=True, readonly=False)
    compute_pack_type_qty = fields.Text(compute="_compute_pack_count", string="No of Packs Pack Type ", store=True,
                                        readonly=False)

    master_shipment_pack_id = fields.Many2one('freight.master.shipment.package', copy=False)
    commodity_ids = fields.One2many('freight.house.package.commodity', 'package_group_id', string='Commodities')
    package_type_id = fields.Many2one(
        'uom.uom', string='Package Type',
        domain=lambda self: "['|', ('transport_mode_ids', '=', transport_mode_id), ('transport_mode_ids', '=', False), ('category_id', '=', %s)]" % self.env.ref(
            'freight_base.product_uom_categ_pack').id)
    part_bl_no_id = fields.Many2one('freight.house.shipment.part.bl')
    sr_no = fields.Integer(string='Sr#', compute='_compute_sr_no')
    sr_container_no = fields.Integer(string='Sr #', compute='_compute_sr_container_no')

    # FLC/LCL package and commodity auto calculate based on weight,volume & Volumetric weight
    total_weight_unit = fields.Float(compute='_compute_total_weight_volume_data', store=True, string="Weight ")
    total_volume_unit = fields.Float(compute='_compute_total_weight_volume_data', store=True, string="Volume ")
    total_volumetric_weight = fields.Float(compute='_compute_total_weight_volume_data', store=True,
                                           string="Volumetric Weight ")

    container_weight_unit_uom_id = fields.Many2one('uom.uom', 'Weight UoM ', compute='_compute_packages_weight_uom',
                                                   store=True)
    container_volume_unit_uom_id = fields.Many2one('uom.uom', 'Volume UoM ', compute='_compute_packages_volume_uom',
                                                   store=True)
    container_volumetric_weight_unit_uom_id = fields.Many2one('uom.uom', 'Container Volumetric Weight UoM',
                                                              compute='_compute_volumetric_weight_uom', store=True)

    hbl_description = fields.Text('HBL Description')

    # Net Weight
    net_weight = fields.Float()
    net_weight_unit_uom_id = fields.Many2one(
        'uom.uom', 'Net Weight UoM',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)],
        default=lambda self: self.get_default_weight_uom())
    total_net_weight = fields.Float(compute='_compute_total_weight_volume_data', store=True, string="Net Weight ")
    container_net_weight_unit_uom_id = fields.Many2one('uom.uom', 'Nett',
                                                       compute='_compute_net_weight_uom', store=True)

    container_package_types = fields.Text(string="Package Types", compute="_compute_container_package_types", store=True)
    commodity_types = fields.Text(string="Commodity Types", compute="_compute_container_package_types", store=True)
    is_part_bl = fields.Boolean('Is Part BL')
    shipment_is_part_bl = fields.Boolean(compute='_compute_shipment_is_part_bl')
    part_bl_domain = fields.Char(compute="_compute_partbl_domain")

    stuffing_date = fields.Date('Stuffing Date')
    stuffing_cfs_id = fields.Many2one("freight.un.location", string="CFS")
    stuffing_confirmed = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Confirmed")
    destuffing_date = fields.Date('DeStuffing Date')
    destuffing_cfs_id = fields.Many2one("freight.un.location", string="CFS")
    destuffing_confirmed = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Confirmed")

    @api.onchange('shipment_id')
    def _compute_shipment_is_part_bl(self):
        for rec in self:
            rec.shipment_is_part_bl = rec.shipment_id.is_part_bl

    @api.depends('shipment_id', 'shipment_id.part_bl_ids')
    def _compute_partbl_domain(self):
        for rec in self:
            rec.part_bl_domain = json.dumps([('id', 'in', rec.shipment_id.part_bl_ids.ids)])

    @api.onchange('is_part_bl')
    def onchange_is_part_bl(self):
        for rec in self:
            rec.container_number.is_part_bl = rec.is_part_bl

    @api.onchange('container_number')
    def onchange_container_number(self):
        for rec in self:
            rec.is_part_bl = rec.container_number.is_part_bl

    is_oog_container = fields.Boolean(related='container_type_id.category_id.is_oog_container', store=True)

    over_lenght = fields.Float('Over Length')
    over_lenght_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)])
    over_height = fields.Float('Over Height')
    over_height_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)])
    over_width = fields.Float('Over Width')
    over_width_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)])
    is_req_loading_handling = fields.Selection([('loading', 'Loading'), ('handling', 'Handling')], 'Is REQ Loading/Handling')
    is_under_deck_requested = fields.Boolean('Is Under Deck Requested')

    @api.depends('shipment_id', 'container_type_id')
    def _compute_allow_container_number(self):
        for rec in self:
            containers = rec.shipment_id.parent_id.carrier_booking_container_ids
            container_number_ids = self.env['freight.master.shipment.container.number']
            if rec.package_mode == 'container':
                containers = containers.filtered_domain([('container_type_id', '=', rec.container_type_id.id)])
                container_number_domain = [
                    '|', ('house_shipment_package_ids', 'in', rec.ids), '&', '&',
                    ('container_type_id', '=', rec.container_type_id.id), ('status', '=', 'unused'),
                    '|', ('house_shipment_package_ids', '=', False),
                    ('house_shipment_package_ids.shipment_id.state', 'in', ['completed', 'cancelled'])
                ]
            else:
                container_number_domain = [
                    '|', ('house_shipment_package_ids.shipment_id', 'in', rec.shipment_id.ids),
                    '&', ('house_shipment_package_ids', '=', False),
                    ('status', '=', 'unused')
                ]
            if not rec.shipment_id.is_part_bl:
                container_number_domain.append(('is_part_bl', '=', False))
            container_number_ids = container_number_ids.search(container_number_domain)
            container_number_ids |= containers.container_number_ids
            if rec.shipment_id.is_part_bl and rec.shipment_id.container_ids.mapped('container_number'):
                container_number_ids |= rec.shipment_id.container_ids.mapped('container_number')
            rec.allow_container_number_ids = [(6, False, container_number_ids.ids)]

    @api.onchange('pack_count')
    def check_pack_count(self):
        for rec in self:
            if rec.pack_count < 0:
                raise ValidationError('Package count should not be negative.')

    @api.depends('package_group_ids', 'package_group_ids.package_type_id', 'package_group_ids.quantity')
    def _compute_pack_count(self):
        for rec in self:
            rec.pack_count = sum(rec.package_group_ids.mapped('quantity'))
            rec.compute_pack_type_qty = ', '.join(["{}{} {}".format(
                pack_group.quantity, pack_group.package_type_id and pack_group.package_type_id.name.split(' ')[0] or '', pack_group.description or '') for pack_group in rec.package_group_ids])

    # @api.constrains('container_number')
    # def _check_container_number_unique(self):
    #     for number in self:
    #         if not number.is_unique_container_number() and not number.shipment_id.cargo_is_package_group:
    #             raise ValidationError(_('Container number should be unique.'))

    # def is_unique_container_number(self):
    #     self.ensure_one()
    #     if not self.container_number:
    #         return True

    #     return self.search_count([
    #         ('container_number.container_number', '=', self.container_number.container_number),
    #         ('shipment_id.state', 'not in', ('cancelled', 'completed'))
    #     ]) <= 1

    def action_open_from_view(self):
        self.ensure_one()
        form_view_id = self.env.ref('freight_management.view_freight_house_shipment_package_form_wizard').id
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

    def action_save(self):
        pass

    @api.depends('shipment_id', 'shipment_id.container_ids', 'shipment_id.package_ids')
    def _compute_sr_container_no(self):
        for rec in self:
            serial_package_no = 1
            serial_container_no = 1
            rec.sr_container_no = 1
            if rec.shipment_id and rec.shipment_id.container_ids or rec.shipment_id.package_ids:
                for line in rec.shipment_id.container_ids:
                    line.sr_container_no = serial_package_no
                    serial_package_no += 1
                for line in rec.shipment_id.package_ids:
                    line.sr_container_no = serial_container_no
                    serial_container_no += 1
            else:
                rec.sr_container_no = serial_package_no or serial_container_no

    @api.depends('container_package_id', 'container_package_id.package_group_ids')
    def _compute_sr_no(self):
        for rec in self:
            serial_no = 1
            rec.sr_no = rec.sr_no or serial_no
            if rec.container_package_id and rec.container_package_id.package_group_ids:
                for line in rec.container_package_id.package_group_ids:
                    line.sr_no = serial_no
                    serial_no += 1
            else:
                rec.sr_no = serial_no

    @api.depends('container_package_id', 'package_group_ids', 'commodity_ids',
                 'commodity_ids.weight_uom_id', 'commodity_ids.volume_uom_id', 'commodity_ids.volumetric_weight_uom_id',
                 'commodity_ids.gross_weight', 'commodity_ids.volume', 'commodity_ids.volumetric_weight',
                 'package_group_ids.weight_unit_uom_id', 'package_group_ids.volume_unit_uom_id', 'package_group_ids.weight_volume_unit_uom_id',
                 'package_group_ids.weight_unit', 'package_group_ids.volume_unit', 'package_group_ids.volumetric_weight',
                 'package_group_ids.net_weight', 'package_group_ids.net_weight_unit_uom_id',
                 'commodity_ids.net_weight', 'commodity_ids.net_weight_unit_uom_id')
    def _compute_total_weight_volume_data(self):
        for rec in self:
            if not rec.container_package_id and rec.package_mode == 'container':
                rec.total_weight_unit = sum([p.weight_unit_uom_id._compute_quantity(p.weight_unit, rec.container_weight_unit_uom_id, round=False) for p in rec.package_group_ids])
                rec.total_volume_unit = sum([p.volume_unit_uom_id._compute_quantity(p.volume_unit, rec.container_volume_unit_uom_id, round=False) for p in rec.package_group_ids])
                rec.total_volumetric_weight = sum([p.weight_volume_unit_uom_id._compute_quantity(p.volumetric_weight, rec.container_volumetric_weight_unit_uom_id) for p in rec.package_group_ids])
                rec.total_net_weight = sum([p.net_weight_unit_uom_id._compute_quantity(p.net_weight, rec.container_net_weight_unit_uom_id) for p in rec.package_group_ids])
            else:
                rec.total_weight_unit = sum([c.weight_uom_id._compute_quantity(c.gross_weight, rec.container_weight_unit_uom_id, round=False) for c in rec.commodity_ids])
                rec.total_volume_unit = sum([c.volume_uom_id._compute_quantity(c.volume, rec.container_volume_unit_uom_id, round=False) for c in rec.commodity_ids])
                rec.total_volumetric_weight = sum([c.volumetric_weight_uom_id._compute_quantity(c.volumetric_weight, rec.container_volumetric_weight_unit_uom_id) for c in rec.commodity_ids])
                rec.total_net_weight = sum([c.net_weight_unit_uom_id._compute_quantity(c.net_weight, rec.container_net_weight_unit_uom_id) for c in rec.commodity_ids])

    @api.depends('container_package_id', 'package_group_ids', 'commodity_ids', 'commodity_ids.weight_uom_id', 'package_group_ids.weight_unit_uom_id')
    def _compute_packages_weight_uom(self):
        for rec in self:
            weight_unit_uom_id = rec.company_id.weight_uom_id
            if not rec.container_package_id and rec.package_mode == 'container' and rec.package_group_ids:
                weight_unit_uom_id = rec.package_group_ids[0].weight_unit_uom_id
            if rec.commodity_ids:
                weight_unit_uom_id = rec.commodity_ids[0].weight_uom_id

            rec.container_weight_unit_uom_id = weight_unit_uom_id.id if weight_unit_uom_id else False

    @api.depends('container_package_id', 'package_group_ids', 'commodity_ids', 'commodity_ids.volume_uom_id', 'package_group_ids.volume_unit_uom_id')
    def _compute_packages_volume_uom(self):
        for rec in self:
            volume_unit_uom_id = rec.company_id.volume_uom_id
            if not rec.container_package_id and rec.package_mode == 'container' and rec.package_group_ids:
                volume_unit_uom_id = rec.package_group_ids[0].volume_unit_uom_id
            if rec.commodity_ids:
                volume_unit_uom_id = rec.commodity_ids[0].volume_uom_id

            rec.container_volume_unit_uom_id = volume_unit_uom_id.id if volume_unit_uom_id else False

    @api.depends('container_package_id', 'package_group_ids', 'commodity_ids', 'commodity_ids.volumetric_weight_uom_id', 'package_group_ids.weight_volume_unit_uom_id')
    def _compute_volumetric_weight_uom(self):
        for rec in self:
            volumetric_weight_unit_uom_id = rec.company_id.weight_uom_id
            if not rec.container_package_id and rec.package_mode == 'container' and rec.package_group_ids:
                volumetric_weight_unit_uom_id = rec.package_group_ids[0].weight_volume_unit_uom_id
            if rec.commodity_ids:
                volumetric_weight_unit_uom_id = rec.commodity_ids[0].volumetric_weight_uom_id

            rec.container_volumetric_weight_unit_uom_id = volumetric_weight_unit_uom_id.id if volumetric_weight_unit_uom_id else False

    @api.depends('container_package_id', 'package_group_ids', 'commodity_ids',
                 'package_group_ids.net_weight_unit_uom_id', 'commodity_ids.net_weight_unit_uom_id')
    def _compute_net_weight_uom(self):
        for rec in self:
            net_weight_unit_uom_id = rec.company_id.weight_uom_id
            if not rec.container_package_id and rec.package_mode == 'container' and rec.package_group_ids:
                net_weight_unit_uom_id = rec.package_group_ids[0].net_weight_unit_uom_id
            if rec.commodity_ids:
                net_weight_unit_uom_id = rec.commodity_ids[0].net_weight_unit_uom_id

            rec.container_net_weight_unit_uom_id = net_weight_unit_uom_id.id if net_weight_unit_uom_id else False

    @api.onchange('weight_unit_uom_id')
    def _onchange_weight_unit_uom_id(self):
        if self.container_package_id and self.package_mode == 'package' and self.container_package_id.container_weight_unit_uom_id:
            if self.weight_unit_uom_id and self.weight_unit_uom_id.id != self.container_package_id.container_weight_unit_uom_id.id:
                self.weight_unit_uom_id = False
                return self.raise_warning_for_uom('Weight', self.container_package_id.container_weight_unit_uom_id.name)

    @api.onchange('volume_unit_uom_id')
    def _onchange_volume_unit_uom_id(self):
        if self.container_package_id and self.package_mode == 'package' and self.container_package_id.container_volume_unit_uom_id:
            if self.volume_unit_uom_id and self.volume_unit_uom_id.id != self.container_package_id.container_volume_unit_uom_id.id:
                self.volume_unit_uom_id = False
                return self.raise_warning_for_uom('Volume', self.container_package_id.container_volume_unit_uom_id.name)

    @api.onchange('weight_volume_unit_uom_id')
    def _onchange_volumetric_weight_uom_id(self):
        if self.container_package_id and self.package_mode == 'package' and self.container_package_id.container_volumetric_weight_unit_uom_id:
            if self.weight_volume_unit_uom_id and self.weight_volume_unit_uom_id.id != self.container_package_id.container_volumetric_weight_unit_uom_id.id:
                self.weight_volume_unit_uom_id = False
                return self.raise_warning_for_uom('Volumetric weight',
                                                  self.container_package_id.container_volumetric_weight_unit_uom_id.name)

    @api.onchange('net_weight_unit_uom_id')
    def _onchange_net_weight_uom_id(self):
        if self.container_package_id and self.package_mode == 'package' and self.container_package_id.container_net_weight_unit_uom_id:
            if self.net_weight_unit_uom_id and self.net_weight_unit_uom_id.id != self.container_package_id.container_net_weight_unit_uom_id.id:
                self.net_weight_unit_uom_id = False
                return self.raise_warning_for_uom('Net weight',
                                                  self.container_package_id.container_net_weight_unit_uom_id.name)

    def raise_warning_for_uom(self, uom_name, package_main_uom):
        warning = {
            'title': _("Warning"),
            'message': _('%s uom should be same for all package to %s.' % (uom_name, package_main_uom))
        }
        return {'warning': warning}

    @api.depends('package_group_ids', 'commodity_ids', 'package_type_id', 'package_group_ids.package_type_id',
                 'commodity_ids.pack_uom_id')
    def _compute_container_package_types(self):
        for house_ship_pack in self:
            packages = []
            commodities = []
            # For FCL
            packages = house_ship_pack.mapped('package_group_ids.package_type_id.name')
            # For LCL
            commodities = house_ship_pack.mapped('commodity_ids.pack_uom_id.name')
            house_ship_pack.container_package_types = ', '.join(list(filter(None, packages)))
            house_ship_pack.commodity_types = ', '.join(list(filter(None, commodities)))

    def copy_data(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if self.shipment_id.cargo_is_package_group:
            default['commodity_ids'] = [(0, 0, commodity_id.copy_data()[0]) for commodity_id in self.commodity_ids]
        return super().copy_data(default=default)


class FreightHouseShipmentPackageItem(models.Model):
    _name = 'freight.house.shipment.package.item'
    _inherit = ['freight.shipment.package.item.mixin']
    _description = 'House Shipment Package Item'

    shipment_package_id = fields.Many2one('freight.house.shipment.package', required=True, ondelete='cascade')
