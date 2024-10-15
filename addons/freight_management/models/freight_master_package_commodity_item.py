from odoo import models, fields, api, _


class FreightMasterPackageCommodity(models.Model):
    _name = 'freight.master.package.commodity'
    _description = 'Master Package Commodity'
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

    commodity_id = fields.Many2one('freight.commodity', 'Commodity', required=True)
    master_package_group_id = fields.Many2one('freight.master.shipment.package', ondelete='cascade')
    shipment_id = fields.Many2one('freight.master.shipment', related="master_package_group_id.shipment_id", store=True)
    house_shipment_commodity_id = fields.Many2one('freight.house.package.commodity', string="House Shipment Commodity", ondelete='cascade')
    transport_mode_id = fields.Many2one(related='shipment_id.transport_mode_id', store=True)
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    is_hazardous = fields.Boolean('Is HAZ', related='commodity_id.hazardous', store=True)
    haz_class_id = fields.Many2one('haz.sub.class.code', 'Haz Class')
    pieces = fields.Integer(related='house_shipment_commodity_id.pieces', readonly=False, store=True)
    pack_uom_id = fields.Many2one(
        related='house_shipment_commodity_id.pack_uom_id', string='Pack UoM', required=True, readonly=False,
        domain=lambda self: [('category_id', '=', self.env.ref('freight_base.product_uom_categ_pack').id)],
        default=get_default_pack_type)
    gross_weight = fields.Float(related='house_shipment_commodity_id.gross_weight', string='Gross Weight',
                                readonly=False, store=True)
    weight_uom_id = fields.Many2one(
        'uom.uom', default=get_default_weight_uom, required=True, related='house_shipment_commodity_id.weight_uom_id',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)],
        readonly=False, store=True)
    volume = fields.Float(related='house_shipment_commodity_id.volume', string='Volume', readonly=False, store=True)
    volume_uom_id = fields.Many2one(
        'uom.uom', default=get_default_volume_uom, required=True, related='house_shipment_commodity_id.volume_uom_id',
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)],
        readonly=False, store=True)
    chargeable_weight = fields.Float(string='Chargeable Weight')
    chargeable_uom_id = fields.Many2one('uom.uom', domain=lambda self: [
        ('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)], default=get_default_weight_uom)
    shipping_bill_no = fields.Char('Shipping Bill No')
    shipping_bill_date = fields.Date('Shipping Bill Date')
    customer_order_no = fields.Char('Customer Order No')
    order_received_date = fields.Date('Order Received Date')
    shipper_ref_number = fields.Char('Shipper Ref Number')
    remarks = fields.Text('Remarks', related='house_shipment_commodity_id.remarks', readonly=False, store=True)
    dimension_uom_id = fields.Many2one(
        "uom.uom", string="UoM", domain=lambda self: [('category_id', '=', self.env.ref('uom.uom_categ_length').id)],
        default=get_default_dimension_uom, required=True, related='house_shipment_commodity_id.dimension_uom_id',
        store=True, readonly=False)
    volumetric_weight = fields.Float(related='house_shipment_commodity_id.volumetric_weight',
                                     string='Volumetric Weight', readonly=False, store=True)
    volumetric_weight_uom_id = fields.Many2one(
        'uom.uom', default=get_default_weight_uom, required=True, readonly=False,
        related='house_shipment_commodity_id.volumetric_weight_uom_id', store=True,
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])
    length = fields.Float(related='house_shipment_commodity_id.length', store=True, readonly=False)
    width = fields.Float(related='house_shipment_commodity_id.width', store=True, readonly=False)
    height = fields.Float(related='house_shipment_commodity_id.height', store=True, readonly=False)
    net_weight = fields.Float(related='house_shipment_commodity_id.net_weight',
                              string='Net Weight', readonly=False, store=True)
    net_weight_unit_uom_id = fields.Many2one(
        'uom.uom', default=get_default_weight_uom, required=True, readonly=False,
        related='house_shipment_commodity_id.net_weight_unit_uom_id', store=True,
        domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_kgm').id)])

    def action_commodity_save(self):
        return

    @api.onchange('weight_uom_id')
    def _onchange_weight_uom_id(self):
        if self.weight_uom_id and self.master_package_group_id.master_commodity_ids and self.weight_uom_id.id != \
                self.master_package_group_id.master_commodity_ids[0].weight_uom_id.id:
            self.weight_uom_id = False
            return self.raise_warning_for_uom('Weight',
                                              self.master_package_group_id.container_master_weight_uom_id.name)

    @api.onchange('volume_uom_id')
    def _onchange_volume_uom_id(self):
        if self.volume_uom_id and self.master_package_group_id.master_commodity_ids and self.volume_uom_id.id != \
                self.master_package_group_id.master_commodity_ids[0].volume_uom_id.id:
            self.volume_uom_id = False
            return self.raise_warning_for_uom('Volume',
                                              self.master_package_group_id.container_master_volume_uom_id.name)

    @api.onchange('volumetric_weight_uom_id')
    def _onchange_volumetric_weight_uom_id(self):
        if (self.volumetric_weight_uom_id and
                self.master_package_group_id.master_commodity_ids and
                self.volumetric_weight_uom_id.id != self.master_package_group_id.master_commodity_ids[
                    0].volumetric_weight_uom_id.id):
            self.volumetric_weight_uom_id = False
            return self.raise_warning_for_uom('Volumetric weight',
                                              self.master_package_group_id.container_master_volumetric_weight_uom_id.name)

    def raise_warning_for_uom(self, uom_name, package_main_uom):
        warning = {
            'title': _("Warning"),
            'message': _('%s uom should be same for all commodity to %s.' % (uom_name, package_main_uom))
        }
        return {'warning': warning}

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

    @api.onchange('net_weight_unit_uom_id')
    def _onchange_net_weight_unit_uom_id(self):
        if (self.net_weight_unit_uom_id and self.master_package_group_id.master_commodity_ids and
                self.net_weight_unit_uom_id.id != self.master_package_group_id.master_commodity_ids[0].net_weight_unit_uom_id.id):
            self.net_weight_unit_uom_id = False
            return self.raise_warning_for_uom('Net weight',
                                              self.master_package_group_id.container_master_net_weight_uom_id.name)