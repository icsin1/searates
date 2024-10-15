# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TariffServiceWizard(models.TransientModel):
    _inherit = 'tariff.service.wizard'

    shipment_quote_id = fields.Many2one('shipment.quote')

    @api.depends('master_shipment_id', 'master_shipment_id.cargo_type_id', 'house_shipment_id', 'house_shipment_id.cargo_type_id', 'shipment_quote_id', 'shipment_quote_id.cargo_type_id')
    def _compute_domain_measurement_basis(self):
        super(TariffServiceWizard, self)._compute_domain_measurement_basis()
        for rec in self.filtered(lambda wiz_rec: wiz_rec.shipment_quote_id):
            cargo_type = rec.shipment_quote_id.cargo_type_id
            if cargo_type.is_package_group:
                domain = [('package_group', 'in', ['all', 'package'])]
            else:
                domain = [('package_group', 'in', ['all', 'container'])]
            rec.domain_measurement_ids = self.env['freight.measurement.basis'].search(domain).ids

    def get_record_date(self):
        self.ensure_one()
        if self.shipment_quote_id:
            return self.shipment_quote_id.date or False
        else:
            return super().get_record_date()

    def get_record(self):
        self.ensure_one()
        if self.shipment_quote_id:
            return self.shipment_quote_id
        else:
            return super().get_record()

    def get_record_company(self):
        self.ensure_one()
        if self.shipment_quote_id:
            return self.shipment_quote_id.company_id
        else:
            return super().get_record_company()

    def get_debtor(self):
        self.ensure_one()
        record = self.get_record()
        if record._name == 'shipment.quote':
            debtor_partner = record.client_id
            debtor_address = record.client_address_id
        else:
            return super().get_debtor()
        return debtor_partner, debtor_address

    def get_record_charges(self):
        self.ensure_one()
        record = self.get_record()
        if record._name == 'shipment.quote':
            RecordObj = self.env['shipment.quote.line']
            record_charges = self.shipment_quote_id.quotation_line_ids
        else:
            return super().get_record_charges()
        return RecordObj, record_charges

    def update_tariff_to_record(self):
        '''Update Buy/Sell/Charge-Master to Quote'''
        if not self.shipment_quote_id:
            return super().update_tariff_to_record()

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

        service_fields = list(self.env['freight.service.mixin']._fields.keys())
        service_fields.extend(['supplier_tax_ids', 'tax_ids'])
        service_fields = [sf for sf in service_fields if hasattr(self.env['tariff.service.line.wizard'], sf)]

        for line in tariff_service_line_ids:
            charge_vals = {}
            charge_vals.update(line._get_charge_vals())
            if line.sell_tariff_line_id:
                # Sell
                charge_vals.update(line._get_sell_charge_vals())
                existing_charge_line = record_charges.filtered(
                    lambda sl: sl.product_id.id == charge_vals['product_id'] and sl.sell_tariff_line_id.id == line.sell_tariff_line_id.id)
                if not existing_charge_line:
                    existing_charge_line = record_charges.filtered(
                        lambda sl: sl.product_id.id == charge_vals['product_id'] and sl.buy_tariff_line_id and not sl.sell_tariff_line_id.id and sl.sell_amount_rate <= 1.0
                    )

            elif line.buy_tariff_line_id:
                # Buy
                charge_vals.update(line._get_buy_charge_vals())
                existing_charge_line = record_charges.filtered(
                    lambda sl: sl.product_id.id == charge_vals['product_id'] and sl.buy_tariff_line_id)
                if not existing_charge_line:
                    existing_charge_line = record_charges.filtered(
                        lambda sl: sl.product_id.id == charge_vals['product_id'] and sl.sell_tariff_line_id and not sl.buy_tariff_line_id.id and sl.cost_amount_rate <= 1.0
                    )
            else:
                # Charge-Master
                existing_charge_line = False
                for field in service_fields:
                    value = line[field]
                    if isinstance(value, models.Model):
                        value = value.id if field.endswith('_id') else value.ids
                    charge_vals.update({field: value})

            if existing_charge_line:
                existing_charge_line = existing_charge_line[0]
                if existing_charge_line.buy_tariff_line_id or existing_charge_line.sell_tariff_line_id:
                    charge_vals.update({'service_name': 'T-{}'.format(existing_charge_line.product_id.name)})
                existing_charge_line.write(charge_vals)
            else:
                existing_line = record_charges.filtered(lambda s: s.product_id.id == line.product_id.id and not s.sell_tariff_line_id and not s.buy_tariff_line_id)
                if not existing_line:
                    existing_line = record_charges.filtered(lambda s: s.product_id.id == line.product_id.id)
                if existing_line and self._context.get('override'):
                    existing_line = existing_line[0]
                    if existing_line.buy_tariff_line_id or existing_line.sell_tariff_line_id:
                        charge_vals.update({'service_name': 'T-{}'.format(existing_line.product_id.name)})
                    existing_line.write(charge_vals)
                else:
                    RecordObj.create(charge_vals)


class TariffServiceLineWizard(models.TransientModel):
    _inherit = 'tariff.service.line.wizard'

    def get_record_specific_val(self):
        self.ensure_one()
        wiz_rec = self.tariff_service_wiz_id
        if wiz_rec.shipment_quote_id:
            vals = {'quotation_id': wiz_rec.shipment_quote_id.id}
        else:
            return super().get_record_specific_val()
        return vals

    def _get_charge_vals(self):
        self.ensure_one()
        vals = self.get_record_specific_val()
        wiz_rec = self.tariff_service_wiz_id
        debtor_partner, debtor_address = wiz_rec.get_debtor()
        if wiz_rec.shipment_quote_id:
            vals.update({
                'sequence': self.sequence,
                'product_id': self.product_id.id,
                'service_name': self.service_name,
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'uom_id': self.uom_id.id,
                'quantity': self.quantity,
                'sell_currency_id': self.sell_currency_id.id,
                'cost_currency_id': self.cost_currency_id.id,
                'measurement_basis_id': self.measurement_basis_id.id,
                'container_type_id': self.container_type_id and self.container_type_id.id or False,
                'debtor_partner_id': debtor_partner and debtor_partner.id,
                'debtor_address_id': debtor_address and debtor_address.id,
            })
        else:
            return super()._get_charge_vals()
        return vals

    def _get_buy_charge_vals(self):
        self.ensure_one()
        wiz_rec = self.tariff_service_wiz_id
        debtor_partner, debtor_address = wiz_rec.get_debtor()
        product = self.product_id
        if wiz_rec.shipment_quote_id:
            return {
                'buy_tariff_line_id': self.buy_tariff_line_id.id,
                'cost_currency_id': self.cost_currency_id.id,
                'cost_conversion_rate': self.cost_conversion_rate,
                'cost_amount_rate': self.cost_amount_rate,
                'sell_amount_rate': 1.0,
                'creditor_partner_id': self.creditor_partner_id.id,
                'creditor_address_id': self.creditor_address_id.id,
                'cost_remarks': self.cost_remarks,
                'property_account_expense_id': self.property_account_expense_id.id,
                'supplier_tax_ids': self.supplier_tax_ids.ids,
                'measurement_basis_id': self.measurement_basis_id.id,
                'debtor_partner_id': debtor_partner and debtor_partner.id,
                'debtor_address_id': debtor_address and debtor_address.id,
                'property_account_income_id': product.property_account_income_id.id or product.categ_id.property_account_income_categ_id.id
            }
        else:
            return super()._get_buy_charge_vals()

    def _get_sell_charge_vals(self):
        self.ensure_one()
        wiz_rec = self.tariff_service_wiz_id
        debtor_partner, debtor_address = wiz_rec.get_debtor()
        if wiz_rec.shipment_quote_id:
            return {
                'sell_tariff_line_id': self.sell_tariff_line_id.id,
                'sell_currency_id': self.sell_currency_id.id,
                'sell_conversion_rate': self.sell_conversion_rate,
                'sell_amount_rate': self.sell_amount_rate,
                'cost_amount_rate': 1.0,
                'debtor_partner_id': debtor_partner and debtor_partner.id,
                'debtor_address_id': debtor_address and debtor_address.id,
                'sell_remarks': self.sell_remarks,
                'property_account_income_id': self.property_account_income_id.id,
                'measurement_basis_id': self.measurement_basis_id.id,
                'tax_ids': self.tax_ids.ids,
            }
        else:
            return super()._get_sell_charge_vals()

    @api.onchange('measurement_basis_id')
    def _onchange_measurement_basis_id(self):
        res = super(TariffServiceLineWizard, self)._onchange_measurement_basis_id()
        teu_measurement_basis = self.env.ref('freight_base.measurement_basis_teu', raise_if_not_found=False)
        container_count_measurement_basis = self.env.ref('freight_base.measurement_basis_container_count', raise_if_not_found=False)
        for line in self.filtered(
                lambda wizard_line: wizard_line.tariff_service_wiz_id.shipment_quote_id and wizard_line.measurement_basis_id in [teu_measurement_basis, container_count_measurement_basis]):
            quantity = 1
            if line.measurement_basis_id == teu_measurement_basis:
                quantity = sum(rec.teu for rec in line.tariff_service_wiz_id.shipment_quote_id.quote_container_line_ids)
            if line.measurement_basis_id == container_count_measurement_basis:
                quantity = sum(rec.count for rec in line.tariff_service_wiz_id.shipment_quote_id.quote_container_line_ids)
            line.quantity = quantity
        return res
