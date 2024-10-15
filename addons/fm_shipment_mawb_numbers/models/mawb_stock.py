# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MAWBStock(models.Model):
    _inherit = 'mawb.stock'

    def action_save_mawb_stock(self):
        self.ensure_one()
        master_shipment_id = self._context.get('default_master_shipment_id')
        if master_shipment_id:
            master_shipment_obj = self.env['freight.master.shipment'].browse(master_shipment_id)
            for line in self.line_ids:
                master_shipment_obj.write({'mawb_stock_line_id': line.id})


class MAWBStockLine(models.Model):
    _inherit = 'mawb.stock.line'

    @api.depends('mawb_stock_id', 'master_shipment_ids', 'master_shipment_ids.state', 'house_shipment_id', 'house_shipment_id.state')
    def _compute_status(self):
        for line in self:
            status = 'available'
            if line.master_shipment_ids and line.master_shipment_ids.filtered(lambda ms: ms.state != 'cancelled'):
                status = "linked"
            elif line.master_shipment_ids.filtered(lambda ms: ms.state != 'cancelled') and not line.house_shipment_id.state != 'cancelled':
                status = "used"
            line.status = status

    master_shipment_id = fields.Many2one('freight.master.shipment', string="Master Shipment")
    house_shipment_id = fields.Many2one('freight.house.shipment', string="House Shipment")
    status = fields.Selection(selection_add=[('used', 'Used'), ('linked', 'Linked')], compute="_compute_status", store=True)
    master_shipment_ids = fields.One2many('freight.master.shipment', 'mawb_stock_line_id', string="Master Shipments")    

    #As we have make changes in master shipment mawb field, action_select_mawb_stock_line and unlink seems not usefuk
    #Need to make sure that what to do if any mawb is going to delete directly from mawb menu and its already used in master shipment 
    def action_select_mawb_stock_line(self):
        master_shipment_id = self._context.get('default_master_shipment_id')
        if master_shipment_id:
            for line in self:
                line.write({
                    'master_shipment_id': master_shipment_id,
                })

    def unlink(self):
        if self._context.get('show_master_shipment'):
            not_linked_line = self.filtered(lambda line: line.status != 'linked')
            if not_linked_line:
                return not_linked_line.write({'master_shipment_id': False})
            else:
                raise ValidationError(_('You can not Remove MAWB Number already linked with House Shipment.'))
        return super(MAWBStockLine, self).unlink()
