# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TariffServiceWizard(models.TransientModel):
    _name = 'tariff.service.wizard'
    _description = 'Tariff Charge'

    def get_charge_category(self):
        return self.env.ref('freight_base.shipment_charge_category', raise_if_not_found=False)

    @api.depends('company_id', 'tariff_for')
    def _compute_charge_domain(self):
        charge_category = self.get_charge_category()
        for rec in self:
            domain = ['|', ('company_id', '=', rec.company_id.id), ('company_id', '=', False)]
            if charge_category:
                domain.append(('categ_id', '=', charge_category.id))
            rec.charge_domain = json.dumps(domain)

    @api.depends('transport_mode_id')
    def _compute_cargo_type_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.cargo_type_domain = json.dumps(domain)

    cargo_type_domain = fields.Char(compute='_compute_cargo_type_domain', store=True)

    @api.depends('master_shipment_id', 'master_shipment_id.cargo_type_id', 'house_shipment_id', 'house_shipment_id.cargo_type_id')
    def _compute_domain_measurement_basis(self):
        for rec in self.filtered(lambda wiz_rec: wiz_rec.house_shipment_id or wiz_rec.master_shipment_id):
            shipment = rec.master_shipment_id or rec.house_shipment_id
            cargo_type = shipment.cargo_type_id  # Get Cargo Type from Shipment House/Master
            if cargo_type.is_package_group:
                domain = [('package_group', 'in', ['all', 'package'])]
            else:
                domain = [('package_group', 'in', ['all', 'container'])]
            rec.domain_measurement_ids = self.env['freight.measurement.basis'].search(domain).ids

    master_shipment_id = fields.Many2one('freight.master.shipment')
    house_shipment_id = fields.Many2one('freight.house.shipment')
    company_id = fields.Many2one('res.company')
    tariff_type = fields.Selection([('buy_tariff', 'Buy'), ('sell_tariff', 'Sell'), ('charge_master', 'From Charge Master')], default='from_charge_master')
    sell_charge_master = fields.Boolean('Sell Charge Master')
    buy_charge_master = fields.Boolean('Buy Charge Master')
    tariff_for = fields.Selection([('shipment', 'Shipment')])

    # Criteria
    ignore_location = fields.Boolean('Skip Location')
    origin_id = fields.Many2one('freight.un.location')
    origin_country_id = fields.Many2one('res.country', related='origin_id.country_id', store=True, string='Origin Country')
    origin_port_id = fields.Many2one('freight.port', domain="[('country_id', '=', origin_country_id), ('transport_mode_id', '=', transport_mode_id)]")
    destination_id = fields.Many2one('freight.un.location')
    destination_country_id = fields.Many2one('res.country', related='destination_id.country_id', store=True, string='Destination Country')
    destination_port_id = fields.Many2one('freight.port', domain="[('country_id', '=', destination_country_id), ('transport_mode_id', '=', transport_mode_id)]")

    shipment_type_id = fields.Many2one('shipment.type')
    transport_mode_id = fields.Many2one('transport.mode')
    cargo_type_id = fields.Many2one('cargo.type')

    customer_id = fields.Many2one('res.partner', domain="['|', ('company_id', '=', company_id), ('company_id', '=', False), ('parent_id', '=', False)]")
    vendor_ids = fields.Many2many(
        'res.partner', domain="[('parent_id', '=', False), ('category_ids.is_vendor', '=', True), '|', ('company_id', '=', company_id), ('company_id', '=', False)]", string="Vendor/Agent")

    tariff_service_line_ids = fields.One2many('tariff.service.line.wizard', 'tariff_service_wiz_id')
    include_all_tariff = fields.Boolean(default=False)
    msg = fields.Char()
    domain_measurement_ids = fields.Many2many(
        'freight.measurement.basis', 'measurement_basis_tariff_line_rel', 'measurement_basis_id', 'wizard_id', compute='_compute_domain_measurement_basis', store=True)

    charge_domain = fields.Char(compute='_compute_charge_domain')
    charge_ids = fields.Many2many(
        'product.product')

    @api.onchange('origin_id')
    def _onchange_origin_id(self):
        if self.origin_country_id != self.origin_port_id.country_id:
            self.origin_port_id = False

    @api.onchange('destination_id')
    def _onchange_destination_id(self):
        if self.destination_country_id != self.destination_port_id.country_id:
            self.destination_port_id = False

    @api.onchange('ignore_location', 'origin_id', 'destination_id', 'shipment_type_id', 'transport_mode_id', 'cargo_type_id', 'customer_id', 'vendor_ids', 'origin_port_id', 'destination_port_id')
    def _onchange_criteria(self):
        self.action_fetch_tariff()

    @api.onchange('charge_ids')
    def _onchange_charges(self):
        self.include_all_tariff = True
        self.action_add_charges()

    def action_fetch_tariff(self):
        self.ensure_one()

        _update_tariff = "_update_{}".format(self.tariff_type)
        if hasattr(self, _update_tariff):
            _update_tariff = getattr(self, _update_tariff)
            # Executing dynamic method based on tariff mode
            self.tariff_service_line_ids = [(5, 0, 0)]
            _update_tariff()

    def get_record_date(self):
        self.ensure_one()
        return (self.house_shipment_id or self.master_shipment_id).shipment_date

    def get_record_company(self):
        self.ensure_one()
        return (self.house_shipment_id or self.master_shipment_id).company_id

    def get_record(self):
        self.ensure_one()
        return self.house_shipment_id or self.master_shipment_id

    def get_buy_tariff_domain(self):
        # Defining Freight Product
        domain = [
            ('buy_tariff_id.tariff_for', '=', self.tariff_for),
            ('buy_tariff_id.shipment_type_id', '=', self.shipment_type_id.id),
            ('buy_tariff_id.transport_mode_id', '=', self.transport_mode_id.id),
            ('buy_tariff_id.cargo_type_id', '=', self.cargo_type_id.id)
        ]

        if self.vendor_ids:
            domain += [('buy_tariff_id.vendor_id', 'in', self.vendor_ids.ids)] + domain

        # Checking for Locations
        if not self.ignore_location:
            domain += [
                '|',
                ('buy_tariff_id.origin_id', '=', self.origin_id.id),
                ('buy_tariff_id.origin_id', '=', False),
                '|',
                ('buy_tariff_id.destination_id', '=', self.destination_id.id),
                ('buy_tariff_id.destination_id', '=', False),
                '|',
                ('buy_tariff_id.origin_port_id', '=', self.origin_port_id.id),
                ('buy_tariff_id.origin_port_id', '=', False),
                '|',
                ('buy_tariff_id.destination_port_id', '=', self.destination_port_id.id),
                ('buy_tariff_id.destination_port_id', '=', False),
            ]

        date = self.get_record_date()
        if date:
            domain += [
                '|',
                ('date_from', '=', False),
                ('date_from', '<=', date),
                '|',
                ('date_to', '=', False),
                ('date_to', '>=', date),
            ]

        company = self.get_record_company()
        if company:
            domain += [('buy_tariff_id.company_id', '=', company.id)]
        return domain

    def _update_buy_tariff(self):
        BuyLineObj = self.env['tariff.buy.line']
        domain = self.get_buy_tariff_domain()
        tariff_lines = BuyLineObj.search(domain)

        if not tariff_lines:
            self.msg = "Couldn't find any active buy Tariff charge line."
            return self.action_open_wizard_again()

        self.msg = False
        self._update_tariff(self.get_record(), tariff_lines, self.tariff_type)

    def get_sell_tariff_domain(self):
        # Defining Freight Product
        domain = [
            ('sell_tariff_id.tariff_for', '=', self.tariff_for),
            ('sell_tariff_id.shipment_type_id', '=', self.shipment_type_id.id),
            ('sell_tariff_id.transport_mode_id', '=', self.transport_mode_id.id),
            ('sell_tariff_id.cargo_type_id', '=', self.cargo_type_id.id)
        ]

        if self.customer_id:
            domain += [('sell_tariff_id.customer_id', '=', self.customer_id.id)] + domain

        # Checking for Locations
        if not self.ignore_location:
            domain += [
                '|',
                ('sell_tariff_id.origin_id', '=', self.origin_id.id),
                ('sell_tariff_id.origin_id', '=', False),
                '|',
                ('sell_tariff_id.destination_id', '=', self.destination_id.id),
                ('sell_tariff_id.destination_id', '=', False),
                '|',
                ('sell_tariff_id.origin_port_id', '=', self.origin_port_id.id),
                ('sell_tariff_id.origin_port_id', '=', False),
                '|',
                ('sell_tariff_id.destination_port_id', '=', self.destination_port_id.id),
                ('sell_tariff_id.destination_port_id', '=', False),
            ]

        date = self.get_record_date()
        if date:
            domain += [
                '|',
                ('date_from', '=', False),
                ('date_from', '<=', date),
                '|',
                ('date_to', '=', False),
                ('date_to', '>=', date),
            ]

        company = self.get_record_company()
        if company:
            domain += [('sell_tariff_id.company_id', '=', company.id)]

        return domain

    def _update_sell_tariff(self):
        SellLineObj = self.env['tariff.sell.line']
        domain = self.get_sell_tariff_domain()
        tariff_lines = SellLineObj.search(domain)

        if not tariff_lines:
            self.msg = "Couldn't find any active sell Tariff charge line."
            return self.action_open_wizard_again()

        self.msg = False
        self._update_tariff(self.get_record(), tariff_lines, self.tariff_type)

    def get_debtor(self):
        self.ensure_one()
        debtor_partner = self.house_shipment_id.client_id if self.house_shipment_id else False
        debtor_address = self.house_shipment_id.client_address_id if self.house_shipment_id else False
        return debtor_partner, debtor_address

    def get_record_charges(self):
        self.ensure_one()
        shipment = self.get_record()
        RecordObj, record_charges = False, False
        if self.tariff_type == 'sell_tariff' or self.sell_charge_master:
            RecordObj = self.env['house.shipment.charge.revenue' if self.house_shipment_id else 'master.shipment.charge.revenue']
            record_charges = shipment.revenue_charge_ids
        elif self.tariff_type == 'buy_tariff' or self.buy_charge_master:
            RecordObj = self.env['house.shipment.charge.cost' if self.house_shipment_id else 'master.shipment.charge.cost']
            record_charges = shipment.cost_charge_ids
        return RecordObj, record_charges

    def _update_tariff(self, record, tariff_lines, mode='sell_tariff'):
        '''Update Tariff Lines to Wizard lines for preview/edit'''
        charge_lines = []

        self.tariff_service_line_ids = [(5, 0, 0)]

        for tariff_line in tariff_lines:
            product = tariff_line.charge_type_id
            values = {
                'currency_id': record.currency_id.id,
                'cost_currency_id': record.currency_id.id,
                'sell_currency_id': record.currency_id.id,
                'service_name': 'T-{}'.format(product.name),
            }
            if mode == 'buy_tariff':
                # Cost
                creditor_partner = tariff_line.buy_tariff_id.vendor_id
                creditor_address = creditor_partner and creditor_partner.child_ids.filtered(lambda c: c.type == 'invoice')
                tariff_cost = tariff_line.unit_price or product.standard_price
                tariff_cost_currency = tariff_line.currency_id.id or record.currency_id.id

                values.update({
                    'tariff_service_wiz_id': self.id,
                    'buy_tariff_line_id': tariff_line.id,
                    'cost_amount_rate': tariff_cost,
                    'measurement_basis_id': tariff_line.measurement_basis_id.id,
                    'cost_currency_id': tariff_cost_currency,
                    'creditor_partner_id': creditor_partner and creditor_partner.id,
                    'creditor_address_id': creditor_address and creditor_address[0].id,
                    'supplier_tax_ids': product.supplier_taxes_id.ids,
                    'property_account_expense_id': product.property_account_expense_id.id or product.categ_id.property_account_expense_categ_id.id,
                    'property_account_income_id': product.property_account_income_id.id or product.categ_id.property_account_income_categ_id.id,
                })
            else:
                # Sell
                debtor_partner = tariff_line.sell_tariff_id.customer_id
                debtor_address = debtor_partner and debtor_partner.child_ids.filtered(lambda c: c.type == 'invoice')
                tariff_sell = tariff_line.unit_price or product.list_price
                tariff_sell_currency = tariff_line.currency_id.id or record.currency_id.id
                values.update({
                    'tariff_service_wiz_id': self.id,
                    'sell_tariff_line_id': tariff_line.id,
                    'sell_amount_rate': tariff_sell,
                    'measurement_basis_id': tariff_line.measurement_basis_id.id,
                    'sell_currency_id': tariff_sell_currency,
                    'debtor_partner_id': debtor_partner and debtor_partner.id,
                    'debtor_address_id': debtor_address and debtor_address[0].id,
                    'tax_ids': product.taxes_id.ids,
                    'property_account_income_id': product.property_account_income_id.id or product.categ_id.property_account_income_categ_id.id,
                })
            charge_lines.append((0, 0, {
                'company_id': record.company_id.id,
                'service_name': 'T-{}'.format(product.name),
                'product_id': product.id,
                'uom_id': product.uom_id.id,
                'quantity': 1.0,
                **values
            }))
        if not charge_lines:
            self.msg = 'There is no Charge lines to update to the Shipment.'
            return self.action_open_wizard_again()

        self.tariff_service_line_ids = charge_lines
        [line.action_update_cost_rate() for line in self.tariff_service_line_ids]
        [line.action_update_sell_rate() for line in self.tariff_service_line_ids]
        [line._onchange_measurement_basis_id() for line in self.tariff_service_line_ids]

    def update_tariff_to_record(self):
        '''Update Buy/Sell/Charge-Master to Shipment'''
        self.msg = False

        # Creditor/Vendor required only in case of Fetch from charge master and Cost-Charge
        invalid_lines = self.tariff_service_line_ids.filtered(lambda a: not a.creditor_partner_id)
        if self.tariff_type == 'charge_master' and self.buy_charge_master and invalid_lines:
            raise ValidationError(_('Please select the vendor/Agent to add the charges.'))

        tariff_service_line_ids = self.tariff_service_line_ids

        if not self.include_all_tariff:
            tariff_service_line_ids = tariff_service_line_ids.filtered(lambda t: t.include_tariff)

        if not tariff_service_line_ids:
            raise ValidationError(_('No charges found to add!'))

        RecordObj, record_charges = self.get_record_charges()
        if not isinstance(RecordObj, models.Model):
            return True

        service_fields = list(self.env['mixin.freight.charge']._fields.keys())
        service_fields.extend(['tax_ids', 'property_account_id'])
        service_fields = [sf for sf in service_fields if hasattr(self.env['tariff.service.line.wizard'], sf)]

        for line in tariff_service_line_ids:
            charge_vals = {}
            charge_vals.update(line._get_charge_vals())
            if line.sell_tariff_line_id:
                # Sell
                charge_vals.update(line._get_sell_charge_vals())
                existing_charge_line = record_charges.filtered(
                    lambda sl: sl.product_id.id == charge_vals['product_id'] and sl.sell_tariff_line_id.id == line.sell_tariff_line_id.id and sl.status not in sl._modification_line_restrict_states())

            elif line.buy_tariff_line_id:
                # Buy
                charge_vals.update(line._get_buy_charge_vals())
                existing_charge_line = record_charges.filtered(
                    lambda sl: sl.product_id.id == charge_vals['product_id'] and sl.buy_tariff_line_id and sl.status not in sl._modification_line_restrict_states())

            else:
                # Charge-Master
                existing_charge_line = False
                if self.buy_charge_master:
                    charge_vals.update(line._get_buy_charge_vals())
                elif self.sell_charge_master:
                    charge_vals.update(line._get_sell_charge_vals())

            if existing_charge_line:
                existing_charge_line = existing_charge_line[0]
                if self.is_tariff_line(existing_charge_line):
                    charge_vals.update({'charge_description': 'T-{}'.format(existing_charge_line.product_id.name)})
                existing_charge_line.write(charge_vals)
            else:
                existing_line = record_charges.filtered(lambda s: s.product_id.id == line.product_id.id and s.status not in s._modification_line_restrict_states())
                if existing_line and self._context.get('override'):
                    existing_line = existing_line[0]
                    if self.is_tariff_line(existing_line):
                        charge_vals.update({'charge_description': 'T-{}'.format(existing_line.product_id.name)})
                    existing_line.write(charge_vals)
                else:
                    RecordObj.create(charge_vals)

    def is_tariff_line(self, line):
        if self.house_shipment_id:
            return True if line._name == 'house.shipment.charge.cost' and line.buy_tariff_line_id or line._name == 'house.shipment.charge.revenue' and line.sell_tariff_line_id else False
        else:
            return True if line._name == 'master.shipment.charge.cost' and line.buy_tariff_line_id or line._name == 'master.shipment.charge.revenue' and line.sell_tariff_line_id else False

    def action_add_charges(self):
        self.ensure_one()
        record = self.get_record()
        ProductObj = self.env['product.product']
        charge_ids = set(self.charge_ids.ids) - set(self.tariff_service_line_ids.mapped('product_id.id'))
        charges_to_add = ProductObj.browse(charge_ids)

        self.tariff_service_line_ids = [(0, 0, {
            'tariff_service_wiz_id': self.id,
            'product_id': charge.id,
            'service_name': charge.name,
            'uom_id': charge.uom_id.id,
            'measurement_basis_id': charge.measurement_basis_id.id,
            'cost_currency_id': record.currency_id.id,
            'sell_currency_id': record.currency_id.id,
            'currency_id': record.currency_id.id,
            'company_id': record.company_id.id,
        }) for charge in charges_to_add]
        # call onchange only for new added lines
        [line._onchange_product_id() for line in self.tariff_service_line_ids.filtered(lambda sl: sl.product_id.id in charges_to_add.ids)]
        [line._onchange_measurement_basis_id() for line in self.tariff_service_line_ids.filtered(lambda sl: sl.product_id.id in charges_to_add.ids)]
        return self.action_open_wizard_again()

    def action_open_wizard_again(self):
        self.ensure_one()
        record_name = self.get_record()
        action = self.env.ref('fm_tariff.tariff_service_wizard_wizard_action').sudo().read()[0]
        action['name'] = '{}: Fetch from {}'.format(record_name, str(self.tariff_type).replace('_', ' ').title())
        action['domain'] = [('id', '=', self.id)]
        action['res_id'] = self.id
        action['context'] = self._context.copy()
        return action


class TariffServiceLineWizard(models.TransientModel):
    _name = 'tariff.service.line.wizard'
    _inherit = ['freight.service.mixin']
    _description = 'Tariff Charge Line'

    tariff_service_wiz_id = fields.Many2one('tariff.service.wizard')
    sell_tariff_line_id = fields.Many2one('tariff.sell.line')
    buy_tariff_line_id = fields.Many2one('tariff.buy.line')

    supplier_tax_ids = fields.Many2many('account.tax', 'freight_service_supp_wiz_tax_default_rel', string='Vendor Taxes')
    tax_ids = fields.Many2many('account.tax', 'freight_service_wiz_tax_default_rel', string='Taxes')
    include_tariff = fields.Boolean(default=False)

    @api.onchange('measurement_basis_id')
    def _onchange_measurement_basis_id(self):
        charges_measure_dict = {
            self.env.ref('freight_base.measurement_basis_chargeable', raise_if_not_found=False): 'chargeable_kg',
            self.env.ref('freight_base.measurement_basis_volume', raise_if_not_found=False): 'volume_unit',
            self.env.ref('freight_base.measurement_basis_weight', raise_if_not_found=False): 'gross_weight_unit'
        }
        teu_measurement_basis = self.env.ref('freight_base.measurement_basis_teu', raise_if_not_found=False)
        container_count_measurement_basis = self.env.ref('freight_base.measurement_basis_container_count', raise_if_not_found=False)
        for line in self:
            wiz_rec = line.tariff_service_wiz_id
            record = wiz_rec.get_record()
            charges_measure_dict.update({
                self.env.ref('freight_base.measurement_basis_chargeable', raise_if_not_found=False): 'chargeable' if record._name == 'shipment.quote' else 'chargeable_kg',
            })
            quantity = 0
            if line.measurement_basis_id:
                column = charges_measure_dict.get(line.measurement_basis_id)
                value = record[column] if column else 1
                quantity = value
            if line.measurement_basis_id == teu_measurement_basis:
                total_teu_count = 1
                if line.tariff_service_wiz_id.house_shipment_id:
                    total_teu_count = sum(rec.container_type_id.total_teu for rec in line.tariff_service_wiz_id.house_shipment_id.container_ids)
                elif line.tariff_service_wiz_id.master_shipment_id:
                    total_teu_count = sum(rec.container_type_id.total_teu for rec in line.tariff_service_wiz_id.master_shipment_id.attached_house_shipment_ids.container_ids)
                quantity = total_teu_count
            if line.measurement_basis_id == container_count_measurement_basis:
                total_container_count = 1
                if line.tariff_service_wiz_id.house_shipment_id:
                    total_container_count = len(line.tariff_service_wiz_id.house_shipment_id.container_ids)
                elif line.tariff_service_wiz_id.master_shipment_id:
                    total_container_count = len(line.tariff_service_wiz_id.master_shipment_id.attached_house_shipment_ids.container_ids)
                quantity = total_container_count
            line.quantity = quantity

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product = self.product_id
        if product:
            wiz_rec = self.tariff_service_wiz_id
            record = wiz_rec.get_record()
            company_currency = record.company_id.currency_id
            self.service_name = product.name
            self.uom_id = product.uom_id
            self.measurement_basis_id = product.measurement_basis_id.id

            self.cost_currency_id = company_currency.id
            self.cost_amount_rate = product.standard_price
            self.tax_ids = product.taxes_id

            self.sell_currency_id = company_currency.id
            self.sell_amount_rate = product.list_price
            self.supplier_tax_ids = product.supplier_taxes_id

            self.property_account_income_id = product.property_account_income_id.id or product.categ_id.property_account_income_categ_id.id
            self.property_account_expense_id = product.property_account_expense_id.id or product.categ_id.property_account_expense_categ_id.id

            debtor_partner, debtor_address = wiz_rec.get_debtor()
            self.debtor_partner_id = debtor_partner and debtor_partner.id
            self.debtor_address_id = debtor_address and debtor_address.id

    def get_record_specific_val(self):
        self.ensure_one()
        wiz_rec = self.tariff_service_wiz_id
        if wiz_rec.house_shipment_id:
            vals = {'house_shipment_id': wiz_rec.house_shipment_id.id}
        else:
            vals = {'master_shipment_id': wiz_rec.master_shipment_id.id}
        return vals

    def _get_charge_vals(self):
        self.ensure_one()
        vals = self.get_record_specific_val()
        vals.update({
            'sequence': self.sequence,
            'product_id': self.product_id.id,
            'charge_description': self.service_name,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'uom_id': self.uom_id.id,
            'quantity': self.quantity,
            'measurement_basis_id': self.measurement_basis_id.id,
            'container_type_id': self.container_type_id and self.container_type_id.id or False
        })
        return vals

    def _get_buy_charge_vals(self):
        self.ensure_one()
        return {
            'buy_tariff_line_id': self.buy_tariff_line_id.id,
            'amount_currency_id': self.cost_currency_id.id,
            'amount_conversion_rate': self.cost_conversion_rate,
            'amount_rate': self.cost_amount_rate,
            'partner_id': self.creditor_partner_id.id,
            'partner_address_id': self.creditor_address_id.id,
            'remarks': self.cost_remarks,
            'property_account_id': self.property_account_expense_id.id,
            'tax_ids': self.supplier_tax_ids.ids,
            'measurement_basis_id': self.measurement_basis_id.id,
        }

    def _get_sell_charge_vals(self):
        self.ensure_one()
        debtor_partner, debtor_address = self.tariff_service_wiz_id.get_debtor()
        return {
            'sell_tariff_line_id': self.sell_tariff_line_id.id,
            'amount_currency_id': self.sell_currency_id.id,
            'amount_conversion_rate': self.sell_conversion_rate,
            'amount_rate': self.sell_amount_rate,
            'partner_id': debtor_partner and debtor_partner.id,
            'partner_address_id': debtor_address and debtor_address.id,
            'remarks': self.sell_remarks,
            'property_account_id': self.property_account_income_id.id,
            'measurement_basis_id': self.measurement_basis_id.id,
            'tax_ids': self.tax_ids.ids,
        }
