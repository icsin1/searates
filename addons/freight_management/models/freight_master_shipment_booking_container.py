# from stdnum.iso6346 import is_valid as is_valid_container_number
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightMasterShipmentCarrierContainer(models.Model):
    _name = 'freight.master.shipment.carrier.container'
    _description = 'Shipment Booking Container'

    @api.model
    def get_default_weight_uom(self):
        return self.env.company.weight_uom_id.id

    @api.model
    def get_default_volume_uom(self):
        return self.env.company.volume_uom_id.id

    shipment_id = fields.Many2one('freight.master.shipment', required=True, ondelete='cascade')
    transport_mode_id = fields.Many2one('transport.mode', related='shipment_id.transport_mode_id', store=True)
    container_type_id = fields.Many2one('freight.container.type', required=True)
    container_count = fields.Integer(default=1, required=True)
    container_mode_id = fields.Many2one('container.service.mode')
    no_of_teu = fields.Integer(compute="_compute_no_of_teu", string="No of TEU", store=True, readonly=True)
    description = fields.Text()
    no_of_packs = fields.Integer()

    weight_unit = fields.Float('Weight', default=None)
    weight_unit_uom_id = fields.Many2one('uom.uom', 'Weight UoM', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)

    volume_unit = fields.Float('Volume', default=None)
    volume_unit_uom_id = fields.Many2one('uom.uom', 'Volume UoM', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)],  default=get_default_volume_uom)

    volumetric_weight = fields.Float(string="Volumetric Weight")
    weight_volume_unit_uom_id = fields.Many2one(
        'uom.uom', 'Volumetric Weight UoM', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)

    is_hazardous = fields.Boolean(default=False, string="Is HAZ")
    un_code = fields.Char(string='UN#')

    # Container Numbers
    container_number_ids = fields.One2many('freight.master.shipment.container.number', 'container_line_id', string='Container Numbers')
    house_shipment_id = fields.Many2one('freight.house.shipment', string="House Shipment")

    # Refrigerated
    is_refrigerated = fields.Boolean(related='container_type_id.category_id.is_refrigerated', store=True)
    container_temperature = fields.Float(string="Min Temperature")
    container_temperature_uom_id = fields.Many2one('uom.uom', domain=lambda self: [
        ('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)])
    max_temperature = fields.Float(string="Max Temperature")
    max_temperature_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)])

    is_oog_container = fields.Boolean(related='container_type_id.category_id.is_oog_container', store=True)

    over_lenght = fields.Float('Over Length')
    over_lenght_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)])
    over_height = fields.Float('Over Height')
    over_height_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)])
    over_width = fields.Float('Over Width')
    over_width_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)])
    is_req_loading_handling = fields.Selection([('loading', 'Loading'), ('handling', 'Handling')],
                                               'Is REQ Loading/Handling')
    is_under_deck_requested = fields.Boolean('Is Under Deck Requested')

    @api.depends('container_count', 'container_type_id')
    def _compute_no_of_teu(self):
        for rec in self:
            rec.no_of_teu = rec.container_count * rec.container_type_id.total_teu

    @api.constrains('container_count', 'container_number_ids')
    def _check_booking_carrier_count(self):
        for container in self:
            if len(container.container_number_ids) > container.container_count:
                raise ValidationError(_('Container Number values are maximum compare to container count.'))


class FreightShipmentContainerNumber(models.Model):
    _name = 'freight.master.shipment.container.number'
    _description = 'Booking Container Number'

    @api.depends('package_ids', 'house_shipment_package_ids', 'house_shipment_package_ids.shipment_id.state', 'shipment_id', 'shipment_id.state')
    def _compute_status(self):
        """
        Unused: Not belongs to any shipment
        Used: Belongs to any shipment + shipment moved ahead [Status Other than Created and Cancelled]
        Linked: Belongs to any shipment, but shipment not moved ahead
        """
        for rec in self:
            status = "unused"
            house_shipments = rec.house_shipment_package_ids.mapped('shipment_id')
            if (house_shipments and house_shipments.filtered(lambda hs: hs.state not in ('created', 'cancelled'))) or (rec.shipment_id and rec.shipment_id.state not in ('draft', 'cancelled')):
                status = "used"
            elif rec.shipment_id or rec.package_ids or rec.house_shipment_package_ids:
                status = "linked"
            if (house_shipments and all(house_shipments.filtered(lambda hs: hs.state in ('completed')))) or (rec.shipment_id and rec.shipment_id.state in ('completed')):
                status = 'unused'
            rec.status = status
            if house_shipments and all(hs.state == 'completed' for hs in house_shipments):
                rec.is_part_bl = False

    name = fields.Char('Name', related='container_number', store=True)
    container_line_id = fields.Many2one('freight.master.shipment.carrier.container')
    container_type_id = fields.Many2one('freight.container.type', related="container_line_id.container_type_id",
                                        store=True, readonly=False)
    container_number = fields.Char('Container Number', required=True)
    package_ids = fields.Many2many('freight.master.shipment.package', string='Linked Packages', compute='_compute_package_ids')
    shipment_id = fields.Many2one('freight.master.shipment', related="container_line_id.shipment_id", store=True)
    sr_no = fields.Integer(string='Sr#', compute='_compute_sr_no')
    seal_number = fields.Char(string='Actual Seal')
    customs_seal_number = fields.Char(string='Customs Seal')
    house_shipment_package_ids = fields.One2many('freight.house.shipment.package', 'container_number',
                                                 string='House Shipment Packages')
    status = fields.Selection([('unused', 'Unused'), ('used', 'Used'), ('linked', 'Linked')],
                              compute="_compute_status", store=True)
    is_part_bl = fields.Boolean('Is Part BL')

    _sql_constraints = [
        ('seal_number_unique', 'CHECK(1=1)', 'IGNORING CONSTRAINT!'),
        ('container_number_unique', 'CHECK(1=1)', 'Container Number must be unique!')
    ]

    @api.model
    def default_get(self, field_list):
        values = super().default_get(fields_list=field_list)
        if 'name' in values:
            values['container_number'] = values.get('name')
        return values

    @api.model
    def name_create(self, name):
        container_number = self.create({'name': name, 'container_number': name})
        return container_number.name_get()[0]

    def _is_duplicate_seal_number(self, seal_number, rec_id=False):
        domain = [('seal_number', '=', seal_number)]
        if rec_id:
            domain.append(('id', '!=', rec_id))
        return bool(self.search_count(domain))

    @api.constrains('seal_number')
    def _check_seal_number(self):
        for rec in self.filtered(lambda r: r.seal_number):
            if self._is_duplicate_seal_number(rec.seal_number, rec.id):
                raise ValidationError(_('%s: The Seal Number must be unique!') % (rec.seal_number))

    def _compute_package_ids(self):
        for rec in self:
            master_shipment = rec.container_line_id.shipment_id
            package_mode = master_shipment.packaging_mode
            packages = master_shipment.container_ids if package_mode == 'container' else master_shipment.package_ids
            packages_with_container = packages.filtered(lambda p: p.container_number.container_number == rec.container_number)
            rec.package_ids = [(6, False, packages_with_container.ids)]

    @api.onchange('container_number')
    @api.constrains('container_number')
    def _check_container_number(self):
        validate_container = self.env['ir.config_parameter'].sudo().get_param('freight_management.container_basic_validation')
        if validate_container:
            for rec in self.filtered(lambda container: container.container_number):
                rec.validate_container_basic_format(rec.container_number)

    @api.model
    def validate_container_basic_format(self, container_number):
        # Validate Container Number Length
        if container_number and len(container_number) < 10:
            raise ValidationError(_('Invalid Container Number:%s. Container number must contains minimum 10 characters') % (container_number))

    @api.model_create_single
    def create(self, values):
        validate_container = self.env['ir.config_parameter'].sudo().get_param('freight_management.container_basic_validation')
        if validate_container and values.get('container_number'):
            self.validate_container_basic_format(values.get('container_number'))
        return super().create(values)

    def write(self, values):
        validate_container = self.env['ir.config_parameter'].sudo().get_param('freight_management.container_basic_validation')
        if validate_container and values.get('container_number'):
            self.validate_container_basic_format(values.get('container_number'))
        return super().write(values)

    # @api.constrains('container_number')
    # def _check_container_number_unique(self):
    #     for number in self:
    #         if not number.is_unique_container_number():
    #             raise ValidationError(_('Container number should be unique and not used on other shipments.'))

    # def is_unique_container_number(self):
    #     self.ensure_one()

    #     if not self.container_number:
    #         return True
    #     if self.shipment_id.carrier_booking_container_ids.container_number_ids.mapped('container_number').count(self.container_number) > 1:
    #         return False

    #     return self.search_count([
    #         ('container_number', '=', self.container_number),
    #         ('shipment_id.state', 'not in', ('cancelled', 'completed'))
    #     ]) <= 1

    def _validate_container_number(self, container_number_list):
        """
        Checks for given container number [type: list]
        returns invalid container number [type: list] if any
        """
        return []

    @api.depends('container_line_id', 'container_line_id.container_number_ids')
    def _compute_sr_no(self):
        for rec in self:
            serial_no = 1
            if rec.container_line_id and rec.container_line_id.container_number_ids:
                for line in rec.container_line_id.container_number_ids:
                    line.sr_no = serial_no
                    serial_no += 1
            else:
                rec.sr_no = serial_no
