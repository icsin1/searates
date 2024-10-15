# -*- coding: utf-8 -*-

from odoo import fields, models, _


class ImportCharges(models.TransientModel):
    _name = 'import.charges'
    _description = "Import Charge Master"

    import_company_id = fields.Many2one('res.company', 'Import Company', required=True, domain=lambda self: [
        ('id', 'in', self.env.user.company_ids.filtered(lambda company: company.id != self.env.company.id).ids)])
    import_price = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='yes', string="Import with Price", required=True)

    def action_import_charge_master(self):
        product_ids = self.env['product.template'].browse(self.env.context.get('product_ids'))
        new_product_count = 0
        exist_product_count = 0
        new_product_list = []
        exist_product_list = []
        currency_exchange_rate = self.env['res.currency']._get_conversion_rate(
            self.env.company.currency_id, self.import_company_id.currency_id, self.import_company_id,fields.Date.today())

        for each in product_ids:
            sale_price = False
            cost_price = False
            if self.import_price == 'yes':
                sale_price = each.currency_id.with_context(
                    currency_exchange_rate=currency_exchange_rate)._convert(
                        each.list_price,self.import_company_id.currency_id,self.import_company_id,fields.Date.today())
                cost_price = each.currency_id.with_context(
                    currency_exchange_rate=currency_exchange_rate)._convert(
                        each.standard_price,self.import_company_id.currency_id,self.import_company_id,fields.Date.today())

            product_vals = {
                'name': each.name,
                'company_id': self.import_company_id.id,
                'detailed_type': each.detailed_type,
                'measurement_basis_id': each.measurement_basis_id.id,
                'charge_type': each.charge_type,
                'categ_id': each.categ_id.id,
                'list_price': sale_price if sale_price else 1,
                'standard_price': cost_price if cost_price else 1,
                'taxes_id': self.import_company_id.account_sale_tax_id
            }
            existing_product_count = self.env['product.template'].sudo().search_count(
                [('name', '=', each.name), ('company_id', '=', self.import_company_id.id)])
            if not existing_product_count:
                self.env['product.template'].sudo().create(product_vals)
                new_product_count += 1
                new_product_list.append(each.name)
            else:
                exist_product_count += 1
                exist_product_list.append(each.name)

        message_id = self.env['import.charge.message'].create({
            'message_for_new_charges': ", ".join(name for name in new_product_list),
            'message_for_existed_charges': ", ".join(name for name in exist_product_list),
            'imported_count': new_product_count,
            'existed_count': exist_product_count}
        )

        return {
            'name': _('Success'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'import.charge.message',
            # pass the id
            'res_id': message_id.id,
            'target': 'new'
        }


class ImportChargeMessage(models.TransientModel):
    _name = 'import.charge.message'
    _description = 'Import Charge Message'

    message_for_new_charges = fields.Text('Charges Imported', readonly=True)
    message_for_existed_charges = fields.Text('Charges Already Exists', readonly=True)
    imported_count = fields.Integer('Imported Count', readonly=True)
    existed_count = fields.Integer('Existed Count', readonly=True)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}
