# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MAWBStock(models.Model):
    _name = 'mawb.stock'
    _description = 'MAWB Stock'

    @api.depends('awb_serial_no', 'airline_id', 'airline_prefix')
    def _compute_display_awb_no(self):
        for stock in self:
            stock.display_awb_no = f'{stock.airline_prefix}-{stock.awb_serial_no}'

    name = fields.Char(compute='_compute_name', store=True)
    home_airport_id = fields.Many2one('freight.port', string='Home Airport', states={'draft': [('readonly', False)]}, readonly=True, required=True, domain="[('transport_mode_type', '=', 'air')]")
    awb_serial_no = fields.Char(string='AWB Serial No', states={'draft': [('readonly', False)]}, readonly=True, required=True)
    borrowed_from_id = fields.Many2one('res.partner', string='Borrowed from', states={'draft': [('readonly', False)]}, readonly=True)
    airline_id = fields.Many2one('freight.carrier', string='Air Line', states={'draft': [('readonly', False)]}, readonly=True, required=True, domain="[('is_air_carrier', '=', True)]")
    airline_prefix = fields.Char(string='Prefix', related='airline_id.airline_prefix', store=True)
    display_awb_no = fields.Char(compute="_compute_display_awb_no", store=True)
    count = fields.Integer(string='No of Count', states={'draft': [('readonly', False)]}, readonly=True, required=True, default=1)
    from_no = fields.Char(string='From No', readonly=True, compute='_compute_from_to', store=True)
    to_no = fields.Char(string='To No', readonly=True, compute='_compute_from_to', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('locked', 'Locked')
    ], string='State', default='draft', states={'draft': [('readonly', False)]}, readonly=True, required=True)
    line_ids = fields.One2many('mawb.stock.line', 'mawb_stock_id', string='Lines', states={'draft': [('readonly', False)]}, readonly=True)

    _sql_constraints = [
        ('awb_no_unique', 'unique(display_awb_no)',
         'AWB Serial No. with airline prefix should be unique!')
    ]

    @api.depends('airline_id', 'awb_serial_no')
    def _compute_name(self):
        for rec in self:
            rec.name = '{} - {}'.format(rec.airline_id.display_name, rec.awb_serial_no)

    @api.depends('line_ids')
    def _compute_from_to(self):
        for stock in self:
            if stock.line_ids:
                stock.from_no = stock.line_ids[0].mawb_number
                stock.to_no = stock.line_ids[-1].mawb_number
            else:
                stock.from_no = False
                stock.to_no = False

    def action_mark_locked(self):
        for stock in self:
            stock.state = 'locked'

    def action_mark_draft(self):
        for stock in self:
            stock.state = 'draft'

    @api.constrains('awb_serial_no')
    def _check_awb_serial_no(self):
        for stock in self:
            if not stock.awb_serial_no or len(stock.awb_serial_no) != 7:
                raise ValidationError(_('Serial Number Must be of 7 Digit'))

    @api.constrains('count')
    def _check_count(self):
        for stock in self:
            if stock.count < 1:
                raise ValidationError(_('No of count must be greater than zero.'))
            if stock.count < len(stock.line_ids.filtered(lambda line: line.status != 'available')):
                raise ValidationError(_("Some MAWB Number already in use, Either change No of Count accordingly or Remove linked MAWB from House/Master Shipment"))

    def write(self, vals):
        res = super().write(vals)
        if ('count' in vals or 'awb_serial_no' in vals) and 'line_ids' not in vals:
            for stock in self:
                lines = stock.generate_lines()
                lines and stock.write({'line_ids': lines})
        return res

    @api.model_create_single
    def create(self, vals):
        res = super().create(vals)
        for stock in res:
            lines = stock.generate_lines()
            lines and stock.write({'line_ids': lines})
        return res

    def generate_lines(self):
        self.ensure_one()

        if not (self.awb_serial_no and self.count):
            return []

        lines = []
        self.line_ids.filtered(lambda x: x.status == 'available').unlink()
        used_lines = self.line_ids.filtered(lambda x: x.status != 'available')
        used_numbers = used_lines.mapped(lambda x: x.sequence_no)
        if not self.awb_serial_no.isdigit():
            raise UserError(_('Invalid Value: Serial Number should be number only'))

        awb_serial_no = int(self.awb_serial_no)
        for i in range(self.count):
            sequence_no = str(awb_serial_no + i)
            if sequence_no in used_numbers:
                continue

            lines.append((0, 0, {
                'sequence_no': sequence_no,
                'mawb_stock_id': self.id,
            }))
        return lines


class MAWBStockLine(models.Model):
    _name = 'mawb.stock.line'
    _description = 'MAWB Stock Line'
    _order = 'sequence_no'
    _rec_name = 'mawb_number'

    @api.depends('mawb_stock_id')
    def _compute_status(self):
        for line in self:
            line.status = "available"

    mawb_stock_id = fields.Many2one('mawb.stock', string='MAWB Stock', required=True, ondelete='cascade')
    sequence_no = fields.Char(string='Sequence No', readonly=True)
    mawb_number = fields.Char(string='MAWB Number', compute='_compute_mawb_number', store=True)
    status = fields.Selection([
        ('available', 'Available'),
    ], string='Status', compute="_compute_status", store=True)

    @api.depends('sequence_no')
    def _compute_mawb_number(self):
        for line in self:
            sequence_no = int(line.sequence_no)
            mawb_number = line.mawb_stock_id.airline_prefix or ''
            mawb_number = "{}{}{}{}".format(mawb_number, mawb_number and '-' or '', sequence_no, sequence_no % 7)
            line.mawb_number = mawb_number
