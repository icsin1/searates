# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    service_job_charge_revenue_id = fields.Many2one('service.job.charge.revenue', copy=False)
    service_job_charge_cost_id = fields.Many2one('service.job.charge.cost', copy=False)
    service_job_id = fields.Many2one('freight.service.job', string='Service Job', compute='_compute_service_job_id', store=True)

    @api.depends('service_job_charge_revenue_id', 'service_job_charge_cost_id')
    def _compute_service_job_id(self):
        for rec in self:
            charge_line = rec.service_job_charge_revenue_id or rec.service_job_charge_cost_id
            rec.service_job_id = charge_line.service_job_id.id

    def copy_data(self, default=None):
        res = super(AccountMoveLine, self).copy_data(default=default)
        if 'move_reverse_cancel' in self.env.context:
            for line, values in zip(self, res):
                values.update({
                    'service_job_charge_cost_id': line.service_job_charge_cost_id.id,
                    'service_job_charge_revenue_id': line.service_job_charge_revenue_id.id,
                    'service_job_id': line.service_job_id.id,
                    'shipment_charge_currency_id': line.shipment_charge_currency_id.id
                })
        return res

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super()._onchange_product_id()
        for line in self.filtered(lambda l: (l.move_id.from_shipment_charge or l.move_id.service_job_ids) and l.product_id and not l.service_job_id):
            return {
                'warning': {
                    'message': _('You are trying to add product in service job {}. This will not effect Service Job Revenue summary.'.format(line.move_id.type_name))
                }
            }

    @api.depends('move_id', 'move_id.state', 'sequence', 'house_shipment_id', 'master_shipment_id', 'service_job_id')
    def _compute_pre_move_line(self):
        job_move_ids = self.mapped('move_id').filtered(lambda m: m.add_charges_from == 'job')
        for move in job_move_ids:
            pre_move_line_id = False
            for line in move.invoice_line_ids.sorted('sequence'):
                if not line.service_job_id:
                    if pre_move_line_id and line.display_type != 'line_section':
                        line.acc_line_doc_id = pre_move_line_id.id
                    else:
                        for ac_line in move.invoice_line_ids.sorted('sequence'):
                            if line.sequence <= ac_line.sequence and ac_line.service_job_id and line.display_type == 'line_section':
                                line.acc_line_doc_id = ac_line.id
                                break
                        if not line.acc_line_doc_id and pre_move_line_id:
                            line.acc_line_doc_id = pre_move_line_id.id
                else:
                    line.acc_line_doc_id = False
                if line.service_job_id:
                    pre_move_line_id = line
        remaining_move_line = self.filtered(lambda m: m.move_id not in job_move_ids.ids)
        if remaining_move_line:
            return super(AccountMoveLine, remaining_move_line)._compute_pre_move_line()
