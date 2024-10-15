from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FreightShipmentPackageMixin(models.AbstractModel):
    _name = 'freight.shipment.package.mixin'
    _description = 'Freight Shipment Package Mixin'
    _rec_name = 'package_mode'

    @api.model
    def get_default_weight_uom(self):
        return self.env.company.weight_uom_id.id

    @api.model
    def get_default_volume_uom(self):
        return self.env.company.volume_uom_id.id

    @api.model
    def get_default_dimension_uom(self):
        return self.env.company.dimension_uom_id.id

    package_mode = fields.Selection([('package', 'Package'), ('container', 'Container')], default='container', required=True)

    # Package if package_mode = Package
    package_type_id = fields.Many2one('uom.uom', string='Package Type', domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)])

    container_type_id = fields.Many2one('freight.container.type')  # Required if packaging_mode = Container
    quantity = fields.Integer(default=1)

    container_number = fields.Many2one('freight.master.shipment.container.number', string='Container #', ondelete='set null')
    no_of_teu = fields.Integer(compute="_compute_no_of_teu", string="No of TEU", store=True, readonly=False)
    seal_number = fields.Char(string='Seal Number', related='container_number.seal_number', store=True, readonly=False)
    customs_seal_number = fields.Char(string='Customs Seal Number', related='container_number.customs_seal_number', store=True, readonly=False)
    description = fields.Text()

    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    dimension_uom_id = fields.Many2one("uom.uom", string="UoM", domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)], default=get_default_dimension_uom)

    weight_unit = fields.Float('Weight', default=None)
    weight_unit_uom_id = fields.Many2one('uom.uom', 'Weight UoM', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)],
                                         default=get_default_weight_uom, required=True)

    volume_unit = fields.Float('Volume', compute='_compute_volume_unit', store=True, readonly=False, default=None, recursive=True)
    volume_unit_uom_id = fields.Many2one('uom.uom', 'Volume UoM', compute='_compute_volume_unit', store=True, readonly=False,
                                         domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)],
                                         default=get_default_volume_uom, recursive=True, required=True)

    volumetric_weight = fields.Float(string="Volumetric Weight", compute='_compute_volumetric_weight', store=True, readonly=False)
    weight_volume_unit_uom_id = fields.Many2one(
        'uom.uom', 'Volumetric Weight UoM', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom, required=True)

    is_hazardous = fields.Boolean(default=False, string="Is HAZ")
    haz_class_id = fields.Many2one('haz.sub.class.code', string='HAZ Class')
    un_code = fields.Char(string='UN#')
    haz_sub_class_id = fields.Many2one('haz.sub.class', string='HAZ Sub Class', domain="[('haz_class_id', '=', haz_class_id)]")
    package_group = fields.Selection([('pack_group_1', 'Package Group |'), ('pack_group_2', 'Package Group ||'), ('pack_group_3', 'Package Group |||')], string="Package Group Type")
    package_info = fields.Many2one('package.info', string='Package Info')
    marine_pollutant = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Marine Pollutant")
    flash_point = fields.Float(string='Flash point')
    ems_number = fields.Char(string='EMS Number')
    emergency_remark = fields.Char(string='Emergency Remark')

    marksnnums = fields.Char(string='MarksnNums', help="The symbols used to identify different pieces of cargo on a ship")

    # Refrigerated
    is_refrigerated = fields.Boolean(related='container_type_id.category_id.is_refrigerated', store=True)
    container_temperature = fields.Float(string="Min Temperature")
    container_temperature_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)])
    max_temperature = fields.Float(string="Max Temperature")
    max_temperature_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_temperature').id)])

    is_oog_container = fields.Boolean(related='container_type_id.category_id.is_oog_container', store=True)

    over_lenght = fields.Float('Over Length')
    over_lenght_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)])
    over_height = fields.Float('Over Height')
    over_height_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)])
    over_width = fields.Float('Over Width')
    over_width_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)])
    is_req_loading_handling = fields.Selection([('loading', 'Loading'), ('handling', 'Handling')], 'Is REQ Loading/Handling')
    is_under_deck_requested = fields.Boolean('Is Under Deck Requested')

    @api.depends('length', 'width', 'height', 'dimension_uom_id', 'volume_unit_uom_id')
    def _compute_volume_unit(self):
        volume_uom = self.env.ref('uom.product_uom_cubic_meter')
        dimension_uom = self.env.ref('uom.product_uom_meter')
        for rec in self:
            length, width, height = rec.length, rec.width, rec.height
            if rec.dimension_uom_id != dimension_uom:
                length = rec.dimension_uom_id._compute_quantity(length, dimension_uom)
                width = rec.dimension_uom_id._compute_quantity(width, dimension_uom)
                height = rec.dimension_uom_id._compute_quantity(height, dimension_uom)
            volume_m3 = length * width * height
            # Convert from M3 to volume-specific weight
            rec_volume_uom = rec.volume_unit_uom_id or volume_uom
            rec.volume_unit, rec.volume_unit_uom_id = volume_uom._compute_quantity(volume_m3, rec_volume_uom), rec_volume_uom.id

    @api.depends('quantity', 'container_type_id')
    def _compute_no_of_teu(self):
        for rec in self:
            rec.no_of_teu = rec.quantity * rec.container_type_id.total_teu if rec.package_mode == 'container' else rec.container_type_id.total_teu

    @api.depends('length', 'height', 'width', 'dimension_uom_id')
    def _compute_volumetric_weight(self):
        uom_cm = self.env.ref('uom.product_uom_cm')
        uom_kg = self.env.ref('uom.product_uom_kgm')
        for rec in self:
            volumetric_divider_value = rec.company_id.volumetric_divider_value or 1
            if rec.dimension_uom_id == uom_cm:
                volumetric_weight_kg = (rec.length * rec.width * rec.height) / volumetric_divider_value
            else:
                from_uom = rec.dimension_uom_id
                volumetric_weight_kg = (
                    from_uom._compute_quantity(rec.length, uom_cm) * from_uom._compute_quantity(rec.width, uom_cm) * from_uom._compute_quantity(rec.height, uom_cm)
                ) / volumetric_divider_value
            # Convert KG to respective Volumetric weight UoM
            volumetric_uom = rec.weight_volume_unit_uom_id
            rec.volumetric_weight = uom_kg._compute_quantity(volumetric_weight_kg, volumetric_uom)

    @api.onchange('container_number')
    def _onchange_container_number(self):
        for rec in self:
            if rec.package_mode == 'package':
                rec.container_type_id = rec.container_number.container_type_id.id

    @api.onchange('haz_class_id')
    def _onchange_haz_class_id(self):
        self.haz_sub_class_id = False

    @api.onchange('quantity')
    def check_quantity(self):
        for rec in self:
            if rec.quantity < 0:
                raise ValidationError('Pack count should not be negative.')


class FreightShipmentPackageItemMixin(models.AbstractModel):
    _name = 'freight.shipment.package.item.mixin'
    _description = 'Shipment Package Item Mixin'

    description = fields.Text(string='Description')
    value = fields.Float(string='Value')
    quantity = fields.Integer(string='Quantity')
