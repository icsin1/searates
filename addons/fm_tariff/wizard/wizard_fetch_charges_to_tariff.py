# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError


class WizardChargeMasterFetch(models.TransientModel):
    _name = "wizard.charge.master.fetch"
    _description = "Charge Master Fetch"

    res_id = fields.Integer(required=True)
    res_model = fields.Char(required=True)
    company_id = fields.Many2one('res.company')
    charge_ids = fields.Many2many(
        'product.product', domain=lambda self: "[('company_id', '=', company_id), ('categ_id', '=', %s)]" % self.env.ref('freight_base.shipment_charge_category').id)

    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        return values

    def action_fetch_and_override(self):
        """ Will update record's line_ids based on selected products
            If Product is already exists, it will override the rates and currency from charge master
            If product is not exists, it will create new line for that record
        """
        if not self.charge_ids:
            raise UserError(_("Please select charges."))
        record = self.env[self.res_model].browse(self.res_id)
        charge_line_list = []
        mapping_dict = {'tariff.buy': 'standard_price', 'tariff.sell': 'lst_price'}
        for line in self.charge_ids:
            existing_tariff_buy_line_ids = record.line_ids.filtered(lambda l: l.charge_type_id.id == line.id)
            unit_price = line[mapping_dict[self.res_model]]
            if existing_tariff_buy_line_ids:
                existing_tariff_buy_line_ids.write({'unit_price': unit_price})
            else:
                charge_line_list.append((0, 0, {'charge_type_id': line.id, 'unit_price': unit_price}))
        if charge_line_list:
            record.write({'line_ids': charge_line_list})

    def action_fetch_and_merge(self):
        """ Will update record's line_ids based on selected products
            If Product is already exists, it will skip the rates and currency for that product
            If product is not exists, it will create new line for that record
        """
        if not self.charge_ids:
            raise UserError(_("Please select charges."))
        record = self.env[self.res_model].browse(self.res_id)
        charge_line_list = []
        existing_products = record.line_ids.mapped('charge_type_id')
        mapping_dict = {'tariff.buy': 'standard_price', 'tariff.sell': 'lst_price'}
        for line in self.charge_ids.filtered(lambda l: l not in existing_products):
            unit_price = line[mapping_dict[self.res_model]]
            charge_line_list.append((0, 0, {'charge_type_id': line.id, 'unit_price': unit_price}))
        if charge_line_list:
            record.write({'line_ids': charge_line_list})
