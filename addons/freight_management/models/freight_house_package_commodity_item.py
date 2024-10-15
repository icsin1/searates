from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class FreightHousePackageCommodity(models.Model):
    _name = 'freight.house.package.commodity'
    _description = 'House Package Commodity'
    _rec_name = 'commodity_id'

    @api.model
    def get_default_pack_type(self):
        return self.env.company.pack_uom_id.id

    @api.model
    def get_default_weight_uom(self):
        return self.env.company.weight_uom_id.id

    @api.model
    def get_default_volume_uom(self):
        return self.env.company.volume_uom_id.id

    @api.model
    def get_default_dimension_uom(self):
        return self.env.company.dimension_uom_id.id

    package_group_id = fields.Many2one('freight.house.shipment.package', ondelete='cascade')
    shipment_id = fields.Many2one('freight.house.shipment', related="package_group_id.shipment_id", store=True)
    company_id = fields.Many2one('res.company', related='shipment_id.company_id', store=True)
    transport_mode_id = fields.Many2one(related='shipment_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    commodity_id = fields.Many2one('freight.commodity', 'Commodity', required=True)
    is_hazardous = fields.Boolean('Is HAZ', related='commodity_id.hazardous', store=True)
    haz_class_id = fields.Many2one('haz.sub.class.code', 'Haz Class')
    pieces = fields.Integer('Pieces')
    pack_uom_id = fields.Many2one(
        'uom.uom', 'Pack UoM', required=True, domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)], default=get_default_pack_type)
    gross_weight = fields.Float('Gross Weight')
    weight_uom_id = fields.Many2one(
        'uom.uom', default=get_default_weight_uom, required=True, domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], ondelete="restrict")
    volume = fields.Float('Volume')
    volume_uom_id = fields.Many2one(
        'uom.uom', default=get_default_volume_uom, required=True, domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)], ondelete="restrict")
    chargeable_weight = fields.Float('Chargeable Weight')
    chargeable_uom_id = fields.Many2one('uom.uom', domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)
    shipping_bill_no = fields.Char('Shipping Bill No')
    shipping_bill_date = fields.Date('Shipping Bill Date')
    customer_order_no = fields.Char('Customer Order No')
    order_received_date = fields.Date('Order Received Date')
    shipper_ref_number = fields.Char('Shipper Ref Number')
    remarks = fields.Text('Remarks')

    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    dimension_uom_id = fields.Many2one(
        "uom.uom", string="UoM", domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)],
        default=get_default_dimension_uom)
    volumetric_weight = fields.Float('Volumetric Weight', readonly=False, compute="_compute_volumetric_weight", store=True)
    volumetric_weight_uom_id = fields.Many2one(
        'uom.uom', default=get_default_weight_uom, required=True,
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], ondelete="restrict")
    master_shipment_comm_id = fields.Many2one('freight.master.package.commodity')

    net_weight = fields.Float('Net Weight')
    net_weight_unit_uom_id = fields.Many2one(
        'uom.uom', 'Net Weight UoM',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)],
        default=get_default_weight_uom)
    chargeable_volume_uom_id = fields.Many2one(
        'uom.uom', default=get_default_volume_uom, required=True, domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)], ondelete="restrict")
    divided_value = fields.Float(string="Divided Value")
    chargeable_volume = fields.Float('Chargeable Volume')
    calculated_dimension_lwh = fields.Boolean(related='shipment_id.calculated_dimension_lwh', store=True)

    @api.onchange('length', 'width', 'height', 'pieces', 'divided_value', 'dimension_uom_id', 'gross_weight')
    def _onchange_sea_volume(self):
        for rec in self:
            if rec.mode_type == 'sea':
                if rec.divided_value:
                    rec.volume = (rec.pieces * rec.length * rec.width * rec.height) / rec.divided_value
                    if rec.gross_weight:
                        weight = (rec.gross_weight / 1000)
                        rec.chargeable_volume = max(rec.volume, weight)
                    else:
                        rec.chargeable_volume = 0.0
                else:
                    rec.volume = 0.0

    @api.depends('length', 'width', 'height', 'pieces', 'divided_value', 'dimension_uom_id')
    def _compute_volumetric_weight(self):
        for rec in self:
            if rec.mode_type in ['air', 'land']:
                if not rec.divided_value:
                    rec.volumetric_weight = 0
                else:
                    rec.volumetric_weight = (rec.length * rec.width * rec.height * rec.pieces) / rec.divided_value
            else:
                rec.volumetric_weight = rec.volumetric_weight

    @api.onchange('dimension_uom_id', 'transport_mode_id')
    def _onchange_uom_transport_mode(self):
        self.divided_value = 0
        if self.transport_mode_id and self.dimension_uom_id:
            volumetric_divided_value = self.env['volumetric.divided.value'].search([
                ('transport_mode_id', '=', self.transport_mode_id.id),
                ('uom_id', '=', self.dimension_uom_id.id)
                ])
            if not volumetric_divided_value:
                raise UserError(
                    ("Divided value for '%s' transport mode and '%s' UOM is not defined.")
                    %(self.transport_mode_id.name, self.dimension_uom_id.name)
                    )
            self.divided_value = volumetric_divided_value.divided_value

    @api.onchange('pieces')
    def onchange_pieces(self):
        for rec in self:
            if rec.pieces < 0:
                raise ValidationError('Pieces should not be negative.')

    def action_open_commodity_from_view(self):
        self.ensure_one()
        return {
            'name': _('Commodities'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit', **self._context},
        }

    def action_commodity_save(self):
        return

    @api.onchange('weight_uom_id')
    def _onchange_weight_uom_id(self):
        if self.weight_uom_id and self.package_group_id.commodity_ids and self.weight_uom_id.id != self.package_group_id.commodity_ids[0].weight_uom_id.id:
            self.weight_uom_id = False
            return self.raise_warning_for_uom('Weight', self.package_group_id.container_weight_unit_uom_id.name)

    @api.onchange('volume_uom_id')
    def _onchange_volume_uom_id(self):
        if self.volume_uom_id and self.package_group_id.commodity_ids and self.volume_uom_id.id != self.package_group_id.commodity_ids[0].volume_uom_id.id:
            self.volume_uom_id = False
            return self.raise_warning_for_uom('Volume', self.package_group_id.container_volume_unit_uom_id.name)

    @api.onchange('volumetric_weight_uom_id')
    def _onchange_volumetric_weight_uom_id(self):
        if self.volumetric_weight_uom_id and self.package_group_id.commodity_ids and self.volumetric_weight_uom_id.id != self.package_group_id.commodity_ids[0].volumetric_weight_uom_id.id:
            self.volumetric_weight_uom_id = False
            return self.raise_warning_for_uom('Volumetric weight', self.package_group_id.container_volumetric_weight_unit_uom_id.name)

    def raise_warning_for_uom(self, uom_name, package_main_uom):
        warning = {
            'title': _("Warning"),
            'message': _('%s uom should be same for all commodity to %s.' % (uom_name, package_main_uom))
            }
        return {'warning': warning}

    @api.onchange('net_weight_unit_uom_id')
    def _onchange_net_weight_uom_id(self):
        if self.net_weight_unit_uom_id and self.package_group_id.commodity_ids and self.net_weight_unit_uom_id.id != \
                self.package_group_id.commodity_ids[0].net_weight_unit_uom_id.id:
            self.net_weight_unit_uom_id = False
            return self.raise_warning_for_uom('Net weight',
                                              self.package_group_id.container_net_weight_unit_uom_id.name)
