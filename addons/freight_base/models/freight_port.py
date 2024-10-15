# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

from odoo.exceptions import ValidationError


class FreightPort(models.Model):
    _name = "freight.port"
    _description = 'Freight Port'
    _rec_name = 'code'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Port Name', required=True)
    country_id = fields.Many2one('res.country', string="Country", required=True)
    coordinates = fields.Char(string='Coordinates')
    phone = fields.Char(string='Phone')
    website = fields.Char(string='Web')
    transport_mode_id = fields.Many2one('transport.mode', required=True)
    transport_mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = ['|', ('name', operator, name), ('code', operator, name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()

    def name_get(self):
        result = []
        for rec in self:
            code_with_country = '%s [%s]' % (rec.code, rec.country_id.name)
            result.append((rec.id, code_with_country))
        return result

    @api.constrains('code')
    def _check_unique_code(self):
        for port in self:
            if port.code:
                domain = [('id', '!=', port.id), ('code', '=ilike', port.code)]
                if self.search_count(domain):
                    raise ValidationError(_('%s port code already exists!' % port.code))
