# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.phone_validation.tools import phone_validation
import re


class Prospect(models.Model):
    _name = "crm.prospect"
    _description = "CRM Prospect"

    name = fields.Char(string='Name', required=True)
    street1 = fields.Char(string='Street1', required=True)
    street2 = fields.Char(string='Street2', required=True)
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', required=True)
    city_id = fields.Many2one('res.city', string='City', domain="[('country_id', '=', country_id)]")
    zip = fields.Char(string="Zip Code")
    phone_no = fields.Char(string="Telephone No")
    contact_name = fields.Char(string="Contact Person")
    designation = fields.Char(string="Designation")
    department = fields.Char(string="Department")
    email = fields.Char(string="Email")
    mobile = fields.Char(string="Mobile")
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    related_partner_id = fields.Many2one('res.partner', string="Related Partner", copy=False)
    category_ids = fields.Many2many('res.partner.type', string="Party Types")
    is_party_type = fields.Boolean('Is Party Type', compute='compute_is_party_type_mandatory')
    is_mandatory = fields.Boolean('Is Mandatory', compute='compute_is_party_type_mandatory')

    @api.constrains('email')
    def _check_email(self):
        for prospect in self:
            if prospect.email:
                prospect_email_unique = self.env['crm.prospect'].sudo().search([
                    ('email', '=', prospect.email), ('id', '!=', prospect.id)])
                if prospect_email_unique:
                    raise ValidationError(_('The same email is already exist!'))

    def compute_is_party_type_mandatory(self):
        for rec in self:
            part_type_selection = self.env['ir.config_parameter'].sudo().get_param('fm_sale_crm.part_type_selection')
            mandatory_fields = self.env['ir.config_parameter'].sudo().get_param('fm_sale_crm.mandatory_fields')
            if part_type_selection:
                rec.is_party_type = True
            else:
                rec.is_party_type = False
            if mandatory_fields:
                rec.is_mandatory = True
            else:
                rec.is_mandatory = False

    @api.model
    def default_get(self, fields):
        defaults = super(Prospect, self).default_get(fields)
        part_type_selection = self.env['ir.config_parameter'].sudo().get_param('fm_sale_crm.part_type_selection')
        mandatory_fields = self.env['ir.config_parameter'].sudo().get_param('fm_sale_crm.mandatory_fields')
        if part_type_selection:
            if (not fields or 'is_party_type' in fields):
                defaults['is_party_type'] = True
        else:
            defaults['is_party_type'] = False
        if mandatory_fields:
            if (not fields or 'is_mandatory' in fields):
                defaults['is_mandatory'] = True
        else:
            defaults['is_mandatory'] = False
        return defaults

    def write(self, vals):
        res = super().write(vals)
        self._check_email()
        return res

    @api.onchange('phone_no', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        if self.phone_no:
            try:
                self.phone_no = self._phone_format(self.phone_no)
            except Exception:
                raise ValidationError(_('Please enter a valid phone number'))

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            try:
                self.mobile = self._phone_format(self.mobile)
            except Exception:
                raise ValidationError(_('Please enter a valid Mobile number'))

    def _phone_format(self, number, country=None, company=None):
        country = country or self.country_id or self.env.company.country_id
        if not country:
            return number
        return phone_validation.phone_format(
            number,
            country.code if country else None,
            country.phone_code if country else None,
            force_format='INTERNATIONAL'
        )

    @api.onchange('country_id')
    def _onchange_country_id(self):
        """
            Upon country onchange set state & city as False if not belongs to the same country.
        """
        if self.country_id:
            self.phone_no = ''
            self.mobile = ''
            if self.country_id != self.state_id.country_id:
                self.state_id = False
            if self.country_id != self.city_id.country_id:
                self.city_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        """
            Upon state onchange set country and reset city if not belongs to the same state.
        """
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id.id
        if self.city_id and self.city_id.state_id != self.state_id:
            self.city_id = False

    @api.onchange('city_id')
    def _onchange_city_id(self):
        """
            Upon City onchange set country, state and zip.
        """
        if self.city_id.state_id:
            self.state_id = self.city_id.state_id.id
        if self.city_id.country_id:
            self.country_id = self.city_id.country_id.id
        self.zip = self.city_id.zipcode

    @api.onchange('email')
    def validate_mail(self):
        if self.email:
            match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,5})$', str(self.email).lower())
            if not match:
                raise ValidationError('Not a valid E-mail ID')

    @api.model
    def get_import_templates(self):
        """
            Add sample CRM Prospect template xls file.
            Returns:list(dict) containing label and template path
        """
        return [{
            'label': _('Import Template for Prospect'),
            'template': '/crm_prospect/static/xls/crm_prospect.xls'
        }]

    def unlink(self):
        for rec in self:
            if rec.lead_count > 0:
                raise UserError(_("Cannot delete a prospect who is linked to a lead."))
        return super(Prospect, self).unlink()
