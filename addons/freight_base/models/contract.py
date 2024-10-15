# -*- coding: utf-8 -*-

from odoo import fields, models


class FreightPartnerContract(models.Model):
    _name = "freight.partner.contract"
    _description = 'Freight Partner Contract'
    _rec_name = 'contract_number'

    contract_number = fields.Char(string='Contract ID', required=True)
    partner_id = fields.Many2one('res.partner', string='Client Organization', required=True)
    origin_location_id = fields.Many2one('freight.un.location', string='Origin')
    destination_location_id = fields.Many2one('freight.un.location', string='Destination')
    date_from = fields.Date(string='Valid From')
    date_to = fields.Date(string='Valid To')
    status = fields.Selection([
        ('new', 'New'),
        ('enable', 'Enabled'),
        ('disable', 'Disabled')
    ], string='Status', default='new')

    _sql_constraints = [
        ('valid_dates_check', "CHECK ((date_from <= date_to))", "The Valid Date From must be before the Valid Date To."),
    ]
