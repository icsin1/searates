# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TariffServiceWizard(models.TransientModel):
    _inherit = 'tariff.service.wizard'
    _description = 'Tariff Charge'

    def get_charge_category(self):
        if self.tariff_for == 'job':
            return self.env.ref('fm_service_job.job_charge_category', raise_if_not_found=False)
        else:
            return super(TariffServiceWizard, self).get_charge_category()

    tariff_for = fields.Selection(selection_add=[('job', 'Service Job')])
    service_job_type_id = fields.Many2one('freight.job.type', ondelete='restrict')
    service_job_id = fields.Many2one('freight.service.job')

    def get_record_date(self):
        self.ensure_one()
        if self.tariff_for == 'job' and self.service_job_id:
            return self.service_job_id.date or False
        else:
            return super().get_record_date()

    def get_record(self):
        self.ensure_one()
        if self.tariff_for == 'job' and self.service_job_id:
            return self.service_job_id
        else:
            return super().get_record()

    def get_record_company(self):
        self.ensure_one()
        if self.tariff_for == 'job' and self.service_job_id:
            return self.service_job_id.company_id
        else:
            return super().get_record_company()

    def get_debtor(self):
        self.ensure_one()
        record = self.get_record()
        if record._name == 'freight.service.job':
            debtor_partner = record.client_id
            debtor_address = record.client_address_id
        else:
            return super().get_debtor()
        return debtor_partner, debtor_address

    def get_record_charges(self):
        self.ensure_one()
        record = self.get_record()
        if self.tariff_for == 'job' and record._name == 'freight.service.job':
            RecordObj, record_charges = False, False
            if self.tariff_type == 'sell_tariff' or self.sell_charge_master:
                RecordObj = self.env['service.job.charge.revenue']
                record_charges = record.revenue_charge_ids
            elif self.tariff_type == 'buy_tariff' or self.buy_charge_master:
                RecordObj = self.env['service.job.charge.cost']
                record_charges = record.cost_charge_ids
            return RecordObj, record_charges
        else:
            return super().get_record_charges()


class TariffServiceLineWizard(models.TransientModel):
    _inherit = 'tariff.service.line.wizard'

    def get_record_specific_val(self):
        self.ensure_one()
        wiz_rec = self.tariff_service_wiz_id
        if wiz_rec.service_job_id:
            vals = {'service_job_id': wiz_rec.service_job_id.id}
        else:
            return super().get_record_specific_val()
        return vals

    @api.onchange('product_id')
    def _onchange_product_id(self):
        wiz_rec = self.tariff_service_wiz_id
        job_measurement = self.env.ref('fm_service_job.measurement_basis_unit', raise_if_not_found=False)
        if wiz_rec.tariff_for == 'job':
            self.measurement_basis_id = job_measurement.id
        else:
            return super()._onchange_product_id()
