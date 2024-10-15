from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightHouseShipmentPartBl(models.Model):
    _name = 'freight.house.shipment.part.bl'
    _description = 'House Shipment Part BL'
    _inherit = ['freight.customer.mixin', 'freight.shipper.mixin', 'freight.consignee.mixin']
    _rec_name = 'bl_no'

    shipment_id = fields.Many2one('freight.house.shipment')
    company_id = fields.Many2one(related='shipment_id.company_id', store=True)
    bl_no = fields.Char('BL No', required=True)
    client_id = fields.Many2one('res.partner', string='Customer')
    client_address_id = fields.Many2one('res.partner', string='Client Address')
    shipper_id = fields.Many2one('res.partner', string='Shipper')
    shipper_address_id = fields.Many2one('res.partner', string='Shipper Address')
    consignee_id = fields.Many2one('res.partner', string='Consignee')
    consignee_address_id = fields.Many2one('res.partner', string='Consignee Address')
    document_type_id = fields.Many2one('freight.document.type', compute="_compute_rmt_report_action")
    report_action_id = fields.Many2one('ir.actions.report', related='document_type_id.report_action_id')

    @api.constrains('bl_no')
    def check_bl_number(self):
        for rec in self:
            part_bl_ids = self.search(
                [('shipment_id.state', '!=', 'cancelled'), ('bl_no', '=', rec.bl_no), ('id', '!=', rec.id)])
            if part_bl_ids:
                raise ValidationError(_('%s: BL number should be unique!') % (part_bl_ids[0].bl_no))

    def _compute_rmt_report_action(self):
        document_type = self.env.ref('freight_management.mtr_part_bl', False)
        for part in self:
            part.document_type_id = document_type and document_type.id or False
