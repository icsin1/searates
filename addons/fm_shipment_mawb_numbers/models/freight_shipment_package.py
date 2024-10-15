from odoo import models, fields, api, _


class FreightMasterShipmentPackageMixin(models.Model):
    _inherit = 'freight.master.shipment.package'

    mawb_stock_line_id = fields.Many2one('mawb.stock.line', string="MAWB", related='shipment_id.mawb_stock_line_id', domain=[('status', '=', 'available')])


class FreightHouseShipmentPackageMixin(models.Model):
    _inherit = 'freight.house.shipment.package'

    @api.depends(
        'shipment_id', 'transport_mode_id', 'mode_type', 'shipment_id.parent_id',
        'shipment_id.parent_id.mawb_stock_line_ids', 'shipment_id.parent_id.mawb_stock_line_ids.status')
    def _compute_available_mawb_stock_line_ids(self):
        for shipment in self:
            master_mawb_stock_line_ids = shipment.shipment_id.parent_id.mawb_stock_line_ids.filtered(lambda line: line.master_shipment_id and not line.house_shipment_id)
            shipment.available_mawb_stock_line_ids = [(6, False, master_mawb_stock_line_ids.ids)]

    mawb_stock_line_id = fields.Many2one('mawb.stock.line', string="MAWB", related='shipment_id.parent_id.mawb_stock_line_id')
    available_mawb_stock_line_ids = fields.Many2many('mawb.stock.line',
                                                     string="availabel MAWB Stock",
                                                     compute="_compute_available_mawb_stock_line_ids")

    def _link_house_to_mawb_stock_line(self):
        self.ensure_one()
        self.mawb_stock_line_id.house_shipment_id = self.shipment_id.id

    def _unlink_house_to_mawb_stock_line(self):
        self.ensure_one()
        self.mawb_stock_line_id.house_shipment_id = False

    @api.model_create_single
    def create(self, vals):
        res = super().create(vals)
        if 'mawb_stock_line_id' in vals and vals.get('mawb_stock_line_id'):
            res._link_house_to_mawb_stock_line()
        return res

    def write(self, vals):
        for package in self:
            if 'mawb_stock_line_id' in vals:
                package._unlink_house_to_mawb_stock_line()
        res = super().write(vals)
        for package in self:
            if 'mawb_stock_line_id' in vals and package.mawb_stock_line_id:
                package._link_house_to_mawb_stock_line()
        return res
