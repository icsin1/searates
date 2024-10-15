from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_company_in_india = fields.Boolean(compute='_compute_is_company_in_india')
    vat_label = fields.Char(
        compute='_compute_dynamic_vat_label',
        string='Dynamic VAT Label',
    )
    l10n_in_pan_number = fields.Char(string='PAN No.', tracking=True)

    @api.depends('company_id', 'company_id.country_id.code')
    def _compute_is_company_in_india(self):
        active_company = self.env.company
        for partner in self:
            is_company_in_india = False
            if active_company.country_id.code == 'IN':
                is_company_in_india = True
            partner.is_company_in_india = is_company_in_india

    @api.depends('country_id')
    def _compute_dynamic_vat_label(self):
        active_company = self.env.company
        for partner in self:
            vat_label = 'VAT'
            if active_company.country_id and active_company.country_id.vat_label:
                vat_label = active_company.country_id.vat_label
            partner.vat_label = vat_label

    def write(self, values):
        res = super().write(values)
        if any(field in values for field in ['l10n_in_pan_number', 'country_id']):
            for record in self:
                if record.is_company_in_india:
                    pan_values = {
                        'l10n_in_pan_number': values.get('l10n_in_pan_number', record.l10n_in_pan_number)
                    }
                    values['l10n_in_pan_number'] = record.validate_pan_number_in(pan_values.get('l10n_in_pan_number'))
        return res

    def validate_pan_number_in(self, pan_number):
        regex = "[A-Z]{5}[0-9]{4}[A-Z]{1}"
        p = re.compile(regex)
        if pan_number:
            if (re.search(p, pan_number) and len(pan_number) == 10):
                return pan_number
            else:
                raise ValidationError('The PAN number %s is not valid.' % pan_number)
        else:
            return False

    @api.onchange('vat')
    def onchange_vat(self):
        res = super(ResPartner, self).onchange_vat()
        pan_number = ''
        if self.vat and len(self.vat) == 15 and self.is_company_in_india:
            pan_number = self.vat[2:12].upper()
        self.l10n_in_pan_number = pan_number
        return res

    @api.model_create_single
    def create(self, values):
        if values.get('l10n_in_pan_number'):
            values['l10n_in_pan_number'] = self.validate_pan_number_in(values.get('l10n_in_pan_number'))
        return super().create(values)
