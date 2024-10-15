# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('partner_id')
    def _compute_allowed_service_job_ids(self):
        ServiceJobRevenueCharge = self.env['service.job.charge.revenue']
        ServiceJobCostCharge = self.env['service.job.charge.cost']
        for move in self:
            allowed_service_job_ids = []
            if move.move_type == "out_invoice":
                charge_ids = ServiceJobRevenueCharge.search([('partner_id', '=', move.partner_id.id), ('status', 'in', ('no', 'partial')), ('company_id', '=', move.company_id.id)])
                allowed_service_job_ids = [(6, 0, charge_ids.mapped('service_job_id.id'))]
            if move.move_type == "in_invoice":
                charge_ids = ServiceJobCostCharge.search([('partner_id', '=', move.partner_id.id), ('status', 'in', ('no', 'partial')), ('company_id', '=', move.company_id.id)])
                allowed_service_job_ids = [(6, 0, charge_ids.mapped('service_job_id.id'))]
            move.allowed_service_job_ids = allowed_service_job_ids

    charge_service_job_ids = fields.Many2many('freight.service.job', 'service_job_account_move_rel', string="Service Job")
    allowed_service_job_ids = fields.Many2many('freight.service.job', 'allowed_service_job_account_move_rel', compute="_compute_allowed_service_job_ids")
    service_job_ids = fields.Many2many('freight.service.job', compute="_compute_service_job", store=True, string='Service Jobs ')
    add_charges_from = fields.Selection(selection_add=[('job', 'Service Job')])

    @api.onchange('add_charges_from')
    def _onchange_add_charges_from(self):
        res = super()._onchange_add_charges_from()
        if self.add_charges_from == 'job':
            self.charge_service_job_ids = [(5, 0, 0)]
        return res

    def action_open_service_job(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('fm_service_job.freight_service_job_action')
        if len(self.service_job_ids) > 1:
            action['domain'] = [('id', 'in', self.service_job_ids.ids)]
            return action

        form_view = [(self.env.ref('fm_service_job.freight_service_job_view_form').id, 'form')]
        action['views'] = form_view + [(state, view) for state, view in action.get('views', []) if view != 'form']
        action['res_id'] = self.service_job_ids.id
        return action

    @api.depends('invoice_line_ids', 'invoice_line_ids.service_job_id')
    def _compute_service_job(self):
        for rec in self:
            if rec.add_charges_from != 'job':
                service_job_ids = False
            else:
                service_job_ids = rec.invoice_line_ids.mapped('service_job_id')
            rec.service_job_ids = [(6, 0, service_job_ids.ids)] if service_job_ids else []

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        result = super(AccountMove, self)._onchange_partner_id()
        if self.state == 'draft' and not self._context.get('skip_reset_line'):
            self.charge_service_job_ids = [(5, 0, 0)]
        return result

    def _create_service_job_revenue_invoice_wizard(self, service_job_id, charges):
        self.ensure_one()
        record = self.env['service.job.charge.invoice.wizard'].create({
            'charge_ids': [(6, False, charges.ids)],
            'service_job_id': service_job_id.id,
            'partner_mode': 'specific',
            'partner_ids': [(6, 0, self.partner_id.ids)],
            'single_currency_billing': True,
            'currency_id': self.currency_id.id,
        })
        record._onchange_field_values()
        record._onchange_currency_id()
        return record

    def _create_service_job_cost_invoice_wizard(self, service_job_id, charges):
        self.ensure_one()
        record = self.env['job.charge.bill.wizard'].create({
            'charge_ids': [(6, False, charges.ids)],
            'service_job_id': service_job_id.id,
            'partner_mode': 'specific',
            'partner_ids': [(6, 0, self.partner_id.ids)],
            'single_currency_billing': True,
            'currency_id': self.currency_id.id,
        })
        record._onchange_field_values()
        record._onchange_currency_id()
        record.action_generate_bill_lines()
        return record

    def add_revenues_from_service_job(self):
        self.ensure_one()
        invoice_lines = []
        self.clear_service_job_from_move_line()
        service_job_charge_invoice_wizard = self.env['service.job.charge.invoice.wizard']
        for service_job in self.charge_service_job_ids:
            charges_to_invoice = service_job.revenue_charge_ids.sudo().filtered(
                lambda line: line.status in ('no', 'partial') and line.company_id.id == self.company_id.id)
            if not charges_to_invoice:
                continue
            service_job_charge_invoice_wizard |= self._create_service_job_revenue_invoice_wizard(service_job, charges_to_invoice)
        if service_job_charge_invoice_wizard:
            for wizard_line_id in service_job_charge_invoice_wizard.line_ids:
                invoice_lines += wizard_line_id._prepare_invoice_line(self.move_type)
        ref = ', '.join(service_job_charge_invoice_wizard.mapped('service_job_id.booking_nomination_no'))
        self.write({
            'invoice_line_ids': invoice_lines,
            'ref': ref,
            'from_shipment_charge': True,
            'invoice_origin': ref,
        })

    def clear_service_job_from_move_line(self):
        for record in self:
            service_job_line = record.invoice_line_ids.filtered(lambda line: line.service_job_id or line.service_job_id.id in record.charge_service_job_ids.ids)
            if service_job_line:
                service_job_line.with_context(check_move_validity=False).unlink()

    def add_cost_from_service_job(self):
        self.ensure_one()
        invoice_lines = []
        self.clear_service_job_from_move_line()
        service_job_charge_bill_wizard = self.env['job.charge.bill.wizard']
        for service_job_id in self.charge_service_job_ids:
            charges_to_bill = service_job_id.cost_charge_ids.filtered(
                lambda line: line.partner_id == self.partner_id and line.status in ('no', 'partial') and line.company_id.id == self.company_id.id)
            if not charges_to_bill:
                continue
            service_job_charge_bill_wizard |= self._create_service_job_cost_invoice_wizard(service_job_id, charges_to_bill)
        if service_job_charge_bill_wizard:
            for wizard_line_id in service_job_charge_bill_wizard.line_ids:
                invoice_lines += wizard_line_id._prepare_invoice_line(self.move_type)
        ref = ', '.join(service_job_charge_bill_wizard.mapped('service_job_id.booking_nomination_no'))
        self.write({
            'invoice_line_ids': invoice_lines,
            'from_shipment_charge': True,
            'invoice_origin': ref,
            'ref': ref
        })

    def write(self, values):
        res = super().write(values)
        for move in self.filtered(lambda move: move.move_type in ('in_invoice', 'out_invoice')):
            if move.add_charges_from == 'job':
                if (values.get('charge_service_job_ids') or values.get('add_charges_from')):
                    move.add_charges_from_house_shipment()
            elif not move.add_charges_from:
                self.clear_service_job_from_move_line()
        return res

    def add_charges_from_house_shipment(self):
        self.ensure_one()
        if self.add_charges_from == 'job':
            if self.move_type == "out_invoice":
                self.add_revenues_from_service_job()
            if self.move_type == "in_invoice":
                self.add_cost_from_service_job()
        else:
            super().add_charges_from_house_shipment()

    def _parse_line_data(self, line, sequence):
        res = super()._parse_line_data(line, sequence)
        if line and line.service_job_id:
            res.update({'service_job_id': line.service_job_id.name})
        return res
