# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CustomerVisitLines(models.Model):
    _name = "customer.visit.lines"
    _description = "Customer Visit Lines"
    _order = 'serial_no'

    name = fields.Char(string='Name')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    customer_id = fields.Many2one('res.partner', related='opportunity_id.customer_id')
    user_id = fields.Many2one("res.users", string="Sales Agent", required=True,
                              default=lambda self: self.env.user)
    opportunity_id = fields.Many2one('crm.prospect.opportunity', string="Opportunity")
    serial_no = fields.Char(string='SR.No', store=True, compute='_compute_auto_serial_no')
    date_of_visit = fields.Date(string='Date')
    time_of_visit = fields.Float(string='Time', digits=(16, 2))
    visited_by_id = fields.Many2one('res.users', domain="[('share', '=', False)]", string="Visited By")
    purpose_of_visit = fields.Char(string='Purpose')
    next_visit = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')], default='no', string='Next Visit')
    communication_mode = fields.Selection([
        ('onsite', 'Onsite'),
        ('virtual meeting', 'Virtual Meeting'),
        ('social media', 'Social Media'),
        ('call', 'Call'),
        ('email', 'Email')], default='', string='Mode of Communication')
    next_followup_date = fields.Date(string='Next Followup Date')
    assign_to_id = fields.Many2one('res.users', domain="[('share', '=', False)]", string="Assign To")
    notes = fields.Text(string='Notes')

    @api.constrains('time_of_visit')
    def _check_time_of_visit(self):
        for record in self:
            if record.time_of_visit > 24:
                raise ValidationError('Time of Visit cannot be greater than 24.')

    @api.model
    def create(self, vals):
        if 'time_of_visit' in vals and vals['time_of_visit'] > 24:
            raise ValidationError('Time of Visit cannot be greater than 24.')
        return super(CustomerVisitLines, self).create(vals)

    def write(self, vals):
        if 'time_of_visit' in vals and vals['time_of_visit'] > 24:
            raise ValidationError('Time of Visit cannot be greater than 24.')
        return super(CustomerVisitLines, self).write(vals)

    @api.depends('opportunity_id.customer_visit_ids')
    def _compute_auto_serial_no(self):
        for record in self:
            serial = 0
            record.serial_no = 0
            for lines in record.opportunity_id.customer_visit_ids:
                serial += 1
                lines.serial_no = serial

    @api.constrains('date_of_visit', 'next_followup_date', 'notes')
    def _check_date(self):
        for visit in self:
            if str(visit.next_followup_date) < str(visit.date_of_visit):
                raise ValidationError("Next Followup Date (%s) should be greater than Date of visit (%s)" % (visit.next_followup_date, visit.date_of_visit))
            if visit.notes:
                if len(visit.notes) > 35:
                    raise ValidationError("Notes (%s) Characters should not be is greater than 35" % visit.notes)
            if visit.date_of_visit < visit.opportunity_id.date:
                raise ValidationError("Date of Visit (%s) should be greater than Opportunity Date (%s)" % (visit.date_of_visit, visit.opportunity_id.date))
