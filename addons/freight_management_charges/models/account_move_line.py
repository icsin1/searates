# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
# from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _order = 'house_shipment_id'

    house_shipment_charge_revenue_id = fields.Many2one('house.shipment.charge.revenue', copy=False)
    house_shipment_charge_cost_id = fields.Many2one('house.shipment.charge.cost', copy=False)
    master_shipment_charge_cost_id = fields.Many2one('master.shipment.charge.cost', copy=False)
    house_shipment_id = fields.Many2one('freight.house.shipment', string='House Shipment', compute='_compute_house_shipment_id', store=True)
    master_shipment_id = fields.Many2one('freight.master.shipment', string='Master Shipment', compute='_compute_master_shipment_id', store=True)
    shipment_charge_currency_id = fields.Many2one('res.currency', copy=False, string='Currency')
    acc_line_doc_id = fields.Many2one('account.move.line', 'Ref for document', compute='_compute_pre_move_line', store=True)
    account_line_doc_ids = fields.One2many('account.move.line', 'acc_line_doc_id')
    booking_reference = fields.Char(related='move_id.booking_reference', store=True)

    @api.depends('move_id', 'move_id.state', 'sequence', 'house_shipment_id', 'master_shipment_id')
    def _compute_pre_move_line(self):
        for move in self.mapped('move_id').filtered(lambda m: m.add_charges_from):
            pre_move_line_id = False
            for line in move.invoice_line_ids.sorted('sequence'):
                if not line.house_shipment_id and not line.master_shipment_id:
                    if pre_move_line_id and line.display_type != 'line_section':
                        line.acc_line_doc_id = pre_move_line_id.id
                    else:
                        for ac_line in move.invoice_line_ids.sorted('sequence'):
                            if line.sequence <= ac_line.sequence and (
                                    ac_line.house_shipment_id or ac_line.master_shipment_id) and line.display_type == 'line_section':
                                line.acc_line_doc_id = ac_line.id
                                break
                        if not line.acc_line_doc_id and pre_move_line_id:
                            line.acc_line_doc_id = pre_move_line_id.id
                else:
                    line.acc_line_doc_id = False
                if line.house_shipment_id or line.master_shipment_id:
                    pre_move_line_id = line

    @api.depends('master_shipment_charge_cost_id')
    def _compute_master_shipment_id(self):
        for rec in self:
            charge_line = rec.master_shipment_charge_cost_id
            rec.master_shipment_id = charge_line.master_shipment_id.id

    @api.depends('house_shipment_charge_revenue_id', 'house_shipment_charge_cost_id')
    def _compute_house_shipment_id(self):
        for rec in self:
            charge_line = rec.house_shipment_charge_revenue_id or rec.house_shipment_charge_cost_id
            rec.house_shipment_id = charge_line.house_shipment_id.id

    def copy_data(self, default=None):
        res = super(AccountMoveLine, self).copy_data(default=default)
        if 'from_reverse' in self.env.context:
            for line, values in zip(self, res):
                values.update({
                    'master_shipment_charge_cost_id': line.master_shipment_charge_cost_id.id,
                    'house_shipment_charge_cost_id': line.house_shipment_charge_cost_id.id,
                    'house_shipment_charge_revenue_id': line.house_shipment_charge_revenue_id.id,
                })
        if 'move_reverse_cancel' in self.env.context:
            for line, values in zip(self, res):
                values.update({
                    'house_shipment_charge_cost_id': line.house_shipment_charge_cost_id.id,
                    'house_shipment_charge_revenue_id': line.house_shipment_charge_revenue_id.id,
                    'house_shipment_id': line.house_shipment_id.id,
                    'shipment_charge_currency_id': line.shipment_charge_currency_id.id
                })
        return res

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super()._onchange_product_id()
        for line in self.filtered(lambda aml: (aml.move_id.from_shipment_charge or aml.move_id.house_shipment_ids) and aml.product_id and not aml.house_shipment_id):
            house_or_master = "house"
            if line.move_id.charge_master_shipment_ids:
                house_or_master = "master"
            return {
                'warning': {
                    'message': _('You are trying to add product in {} shipment {}. This will not effect Shipment Revenue summary.'.format(house_or_master, line.move_id.type_name))
                }
            }
