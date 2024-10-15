# -*- coding: utf-8 -*-

from odoo import models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _create_per_company_freight_sequence(self):
        super()._create_per_company_freight_sequence()
        company_sequence = self.env.ref('fm_proforma.sequence_pro_forma_invoice')
        if company_sequence.company_id != self:
            company_sequence = company_sequence.copy({'company_id': self.id})
        self.env['freight.sequence'].create({
            'name': 'Pro Forma Invoice',
            'ir_model_id': self.env.ref('fm_proforma.model_pro_forma_invoice').id,
            'ir_field_id': self.env.ref('fm_proforma.field_pro_forma_invoice__name').id,
            'ir_sequence_id': company_sequence.id,
            'sequence_format': 'PRO',
            'number_increment': 1,
            'padding': 5,
            'company_id': self.id
        })
