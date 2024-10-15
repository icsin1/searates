from odoo import models, fields, api, _
from odoo.tools import format_decimalized_amount
from odoo.exceptions import ValidationError


class FreightServiceJobCharges(models.Model):
    _name = 'freight.service.job'
    _inherit = ['freight.service.job', 'shipment.profitability.mixin']

    # Revenue
    revenue_charge_ids = fields.One2many('service.job.charge.revenue', 'service_job_id', string='Revenue Charges')
    revenue_charge_count = fields.Integer(compute='_compute_revenue_charge_count', store=True)
    revenue_charge_amount = fields.Monetary(compute='_compute_revenue_charge_amount', store=True)
    revenue_charge_state_info = fields.Char(compute='_compute_revenue_charge_state_info', store=True)

    # Cost
    cost_charge_ids = fields.One2many('service.job.charge.cost', 'service_job_id', string='Cost Charges')
    cost_charge_count = fields.Integer(compute='_compute_cost_charge_count', store=True)
    cost_charge_amount = fields.Monetary(compute='_compute_cost_charge_amount', store=True)
    cost_charge_state_info = fields.Char(compute='_compute_cost_charge_state_info', store=True)

    # Accounting
    move_line_ids = fields.One2many('account.move.line', 'service_job_id', string='Moves Lines')
    move_ids = fields.Many2many('account.move', compute='_compute_account_moves_count', store=True, string='Moves')
    invoice_count = fields.Integer(compute='_compute_account_moves_count', store=True)
    vendor_bill_count = fields.Integer(compute='_compute_account_moves_count', store=True)
    credit_note_count = fields.Integer(compute='_compute_account_moves_count', store=True)
    debit_note_count = fields.Integer(compute='_compute_account_moves_count', store=True)

    # Profitability
    # Estimated vs Received
    estimated_revenue = fields.Monetary(string='Estimated Revenue', compute='_compute_estimated_revenue', store=True)
    estimated_cost = fields.Monetary(string='Estimated Cost', compute='_compute_estimated_cost', store=True)
    received_revenue = fields.Monetary(string='Revenue Received', compute='_compute_received_revenue', store=True)
    paid_cost = fields.Monetary(string='Cost Paid', compute='_compute_paid_cost', store=True)

    @api.depends('move_line_ids')
    def _compute_account_moves_count(self):
        for rec in self:
            move_lines = rec.move_line_ids
            rec.move_ids = [(6, False, move_lines.mapped('move_id').ids)]
            rec.invoice_count = len(rec.move_ids.filtered(lambda l: l.move_type == 'out_invoice'))
            rec.vendor_bill_count = len(rec.move_ids.filtered(lambda l: l.move_type == 'in_invoice'))
            rec.credit_note_count = len(rec.move_ids.filtered(lambda l: l.move_type == 'out_refund'))
            rec.debit_note_count = len(rec.move_ids.filtered(lambda l: l.move_type == 'in_refund'))

    @api.depends('revenue_charge_ids')
    def _compute_revenue_charge_count(self):
        for rec in self:
            rec.revenue_charge_count = len(rec.revenue_charge_ids)

    def write(self, vals):
        for rec in self:
            if vals.get('company_id') and rec.revenue_charge_ids and rec.revenue_charge_ids.filtered(lambda r: r.company_id.id != vals.get('company_id')):
                raise ValidationError(_('You can not change company once charges are added'))
            if vals.get('company_id') and rec.cost_charge_ids and rec.cost_charge_ids.filtered(lambda c: c.company_id.id != vals.get('company_id')):
                raise ValidationError(_('You can not change company once charges are added'))
        return super().write(vals)

    @api.depends('revenue_charge_ids', 'revenue_charge_ids.total_amount')
    def _compute_revenue_charge_amount(self):
        for rec in self:
            rec.revenue_charge_amount = sum(rec.revenue_charge_ids.mapped('total_amount'))

    @api.depends('revenue_charge_amount', 'revenue_charge_count')
    def _compute_revenue_charge_state_info(self):
        for rec in self:
            amount_display = format_decimalized_amount(rec.revenue_charge_amount, rec.currency_id)
            rec.revenue_charge_state_info = "{} ({})".format(amount_display, rec.revenue_charge_count)

    @api.depends('cost_charge_ids')
    def _compute_cost_charge_count(self):
        for rec in self:
            rec.cost_charge_count = len(rec.cost_charge_ids)

    @api.depends('cost_charge_ids', 'cost_charge_ids.total_amount')
    def _compute_cost_charge_amount(self):
        for rec in self:
            rec.cost_charge_amount = sum(rec.cost_charge_ids.mapped('total_amount'))

    @api.depends('cost_charge_amount', 'cost_charge_count')
    def _compute_cost_charge_state_info(self):
        for rec in self:
            amount_display = format_decimalized_amount(rec.cost_charge_amount, rec.currency_id)
            rec.cost_charge_state_info = "{} ({})".format(amount_display, rec.cost_charge_count)

    def action_open_moves(self):
        self.ensure_one()
        move_type = self.env.context.get('move_type')
        if not move_type or move_type == 'entry':
            return
        invoices = self.move_ids.filtered(lambda l: l.move_type == move_type)
        if not invoices:
            return
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_%s_type" % (move_type))
        action['context'] = {'default_service_job_id': self.id, 'default_move_type': move_type, 'create': 0}

        if len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
        return action

    @api.depends('revenue_charge_ids', 'revenue_charge_ids.total_amount')
    def _compute_estimated_revenue(self):
        for service_job in self:
            service_job.estimated_revenue = sum(service_job.revenue_charge_ids.mapped('total_amount'))

    @api.depends('cost_charge_ids', 'cost_charge_ids.total_amount')
    def _compute_estimated_cost(self):
        for service_job in self:
            service_job.estimated_cost = sum(service_job.cost_charge_ids.mapped('total_amount'))

    @api.depends('revenue_charge_ids', 'revenue_charge_ids.total_amount', 'revenue_charge_ids.amount_currency_residual')
    def _compute_received_revenue(self):
        for service_job in self:
            total_amount = sum(service_job.revenue_charge_ids.mapped('total_amount'))
            due_amount = sum(service_job.revenue_charge_ids.mapped('total_residual_amount'))
            service_job.received_revenue = round(total_amount - due_amount, 3)

    @api.depends('cost_charge_ids', 'cost_charge_ids.total_amount', 'cost_charge_ids.amount_currency_residual')
    def _compute_paid_cost(self):
        for service_job in self:
            total_amount = sum(service_job.cost_charge_ids.mapped('total_amount'))
            due_amount = sum(service_job.cost_charge_ids.mapped('total_residual_amount'))
            service_job.paid_cost = round(total_amount - due_amount, 3)

    def unlink(self):
        for service_job in self:
            billed_cost_charge_ids = service_job.cost_charge_ids\
                .filtered(lambda charge: charge.status in ['partial', 'fully_billed'])
            invoiced_revenue_charge_ids = service_job.revenue_charge_ids\
                .filtered(lambda charge: charge.status in ['partial', 'fully_invoiced'])
            if billed_cost_charge_ids or invoiced_revenue_charge_ids:
                raise ValidationError(_("You cannot do this modification on a service job "
                                        "after charges are invoiced/billed."))
        return super().unlink()
