from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ContainerType(models.Model):
    _name = "freight.container.type"
    _description = "Container/Package Type"
    _rec_name = 'display_name'

    @api.model
    def get_default_weight_uom(self):
        return self.env.company.weight_uom_id.id

    @api.model
    def get_default_volume_uom(self):
        return self.env.company.volume_uom_id.id

    @api.model
    def get_default_transport_mode(self):
        return self.env.ref('freight_base.transport_mode_sea')

    display_name = fields.Char(compute='_compute_display_name', store=True)
    code = fields.Char(required=True)
    name = fields.Char("Description", required=True)
    category_id = fields.Many2one("freight.container.category", string="Container Category")
    tare_weight = fields.Float()
    tare_weight_uom_id = fields.Many2one(
        "uom.uom", string="Tare Weight Unit", domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)
    max_gross_weight = fields.Float()
    max_gross_weight_uom_id = fields.Many2one(
        "uom.uom", string="Max Gross Unit", domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)
    max_cargo_weight = fields.Float()
    max_cargo_weight_uom_id = fields.Many2one(
        "uom.uom", string="Max Cargo Unit", domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)
    net_weight = fields.Float()
    net_weight_uom_id = fields.Many2one(
        "uom.uom", string="Net Weight Unit", domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)
    cubic_capacity = fields.Float()
    cubic_capacity_uom_id = fields.Many2one(
        "uom.uom", string="Cubic Capacity Unit", domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)], default=get_default_volume_uom)
    total_teu = fields.Integer("TEU")
    iata_class = fields.Char("IATA Class")
    outer_length = fields.Float()
    outer_breadth = fields.Float()
    outer_height = fields.Float()
    outer_uom_id = fields.Many2one("uom.uom", string="Outer Measurement Unit")
    inner_length = fields.Float()
    inner_breadth = fields.Float()
    inner_height = fields.Float()
    inner_uom_id = fields.Many2one("uom.uom", string="Inner Measurement Unit")
    active = fields.Boolean(default=True)
    transport_mode_id = fields.Many2one('transport.mode', default=get_default_transport_mode)

    _sql_constraints = [
        ('iata_class_uniq', 'unique (iata_class)', 'The IATA Class must be unique!')
    ]

    @api.constrains('total_teu')
    def _check_teu(self):
        for record in self:
            if record.total_teu <= 0:
                raise ValidationError(_('Invalid value! The TEU should only accept values greater than zero.'))
            if record.total_teu > 2:
                raise ValidationError(_('Invalid value! The TEU should only accept max value per should be 2.'))

    @api.depends("name", "code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[{}] {}'.format(rec.code, rec.name)
