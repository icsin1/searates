# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ShipmentQuoteLine(models.Model):
    _name = "shipment.quote.line"
    _inherit = ['freight.service.mixin']
    _description = "Quote Charges"
    _rec_name = 'service_name'
    _check_company_auto = True

    quotation_id = fields.Many2one('shipment.quote', string='Shipment Quote', required=True, ondelete='cascade', copy=False)
    supplier_tax_ids = fields.Many2many('account.tax', 'supplier_quote_line_tax_default_rel', string='Vendor Taxes', copy=False,
                                        domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]")
    tax_ids = fields.Many2many('account.tax', 'quote_line_tax_default_rel', string='Taxes', copy=False, domain="[('company_id', '=', company_id),('type_tax_use', '=', 'sale')]")
    include_charges = fields.Boolean('Include Charges', default=True)
    allowed_partner_ids = fields.Many2many('res.partner', compute='_compute_allowed_partner_ids')
    debtor_partner_id = fields.Many2one('res.partner', string='Debtor', tracking=True, domain="[('id', 'in', allowed_partner_ids)]")
    domain_measurement_ids = fields.Many2many('freight.measurement.basis', string='Domain Measurement Basis', compute='_compute_domain_measurement_basis', store=True)
    charge_note = fields.Char(string='Charge Note')
    @api.depends('quotation_id', 'quotation_id.shipper_id', 'quotation_id.consignee_id')
    def _compute_allowed_partner_ids(self):
        for rec in self:
            partners = (rec.quotation_id.shipper_id + rec.quotation_id.consignee_id + rec.quotation_id.client_id)
            rec.allowed_partner_ids = [(6, False, partners.ids)]

    @api.depends('quotation_id', 'quotation_id.cargo_type_id')
    def _compute_domain_measurement_basis(self):
        for rec in self:
            cargo_type_id = rec.quotation_id.cargo_type_id
            domain = [('package_group', '=', 'all')]
            if cargo_type_id.is_package_group:
                domain = [('package_group', 'in', ['all', 'package'])]
            if not cargo_type_id.is_package_group:
                domain = [('package_group', 'in', ['all', 'container'])]
            rec.domain_measurement_ids = self.env['freight.measurement.basis'].search(domain).ids

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product = self.product_id
        if product:
            accounts = product.with_company(self.company_id)._get_product_accounts()
            company_currency = self.company_id.currency_id
            self.service_name = product.name
            self.uom_id = product.uom_id
            self.measurement_basis_id = product.measurement_basis_id.id

            self.cost_currency_id = company_currency
            self.cost_amount_rate = product.standard_price
            self.tax_ids = product.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)

            self.sell_currency_id = company_currency
            self.sell_amount_rate = product.list_price
            self.supplier_tax_ids = product.supplier_taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)

            self.property_account_income_id = accounts['income']
            self.property_account_expense_id = accounts['expense']

    @api.onchange('measurement_basis_id', 'container_type_id')
    def _onchange_measurement_basis_id(self):
        charges_measure_dict = {self.env.ref('freight_base.measurement_basis_chargeable', raise_if_not_found=False): 'chargeable',
                                self.env.ref('freight_base.measurement_basis_volume', raise_if_not_found=False): 'volume_unit',
                                self.env.ref('freight_base.measurement_basis_weight', raise_if_not_found=False): 'gross_weight_unit',
                                self.env.ref('freight_base.measurement_basis_wm', raise_if_not_found=False): 'chargeable_volume'
                                }
        if self.measurement_basis_id and self.quotation_id:
            column = charges_measure_dict.get(self.measurement_basis_id)
            self.quantity = self.quotation_id[column] if column else 1
            if self.measurement_basis_id == self.env.ref('freight_base.measurement_basis_teu'):
                total_teu_count = sum(line.teu for line in self.quotation_id.quote_container_line_ids)
                self.quantity = total_teu_count
            if self.measurement_basis_id == self.env.ref('freight_base.measurement_basis_container_count'):
                total_container_count = sum(line.count for line in self.quotation_id.quote_container_line_ids)
                self.quantity = total_container_count

    @api.onchange('container_type_id')
    def _onchange_container_type_id(self):
        for charge in self:
            if charge.is_container_type_basis and charge.container_type_id:
                containers = charge.quotation_id.quote_container_line_ids
                selected_container_type = charge.container_type_id.id
                filtered_containers = containers.filtered(lambda c: c.container_type_id.id == selected_container_type)
                charge.quantity = sum(filtered_containers.mapped('count'))

            if self.measurement_basis_id == self.env.ref('freight_base.measurement_basis_teu'):
                total_teu_count = sum(self.quotation_id.quote_container_line_ids.mapped('teu'))
                self.quantity = total_teu_count

            if self.measurement_basis_id == self.env.ref('freight_base.measurement_basis_container_count'):
                total_container_count = sum(self.quotation_id.quote_container_line_ids.mapped('count'))
                self.quantity = total_container_count

            if self.is_container_type_basis and self.container_type_id:
                total_container_count = sum(self.quotation_id.quote_container_line_ids.filtered(
                    lambda container: container.container_type_id.id == self.container_type_id.id).mapped('count'))
                self.quantity = total_container_count

    @api.onchange('creditor_partner_id')
    def _onchange_creditor_partner_id(self):
        self.creditor_address_id = False
        if self.creditor_partner_id:
            address = self.creditor_partner_id.get_default_addresses()
            self.creditor_address_id = address and address[0]

    @api.onchange('debtor_partner_id')
    def _onchange_debtor_partner_id(self):
        self.debtor_address_id = False
        if self.debtor_partner_id:
            address = self.debtor_partner_id.get_default_addresses()
            self.debtor_address_id = address and address[0]
