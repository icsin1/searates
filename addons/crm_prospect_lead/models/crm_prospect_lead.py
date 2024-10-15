# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.phone_validation.tools import phone_validation
import re
import json


class ProspectLead(models.Model):
    _name = "crm.prospect.lead"
    _description = "Prospect Lead"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _segment_key = 'leads'

    @api.depends('transport_mode_id', 'origin_country_id')
    def _compute_port_of_loading_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            if rec.origin_country_id:
                domain.append(('country_id', '=', rec.origin_country_id.id))
            rec.port_of_loading_domain = json.dumps(domain)

    port_of_loading_domain = fields.Char(compute='_compute_port_of_loading_domain', store=True)

    @api.depends('transport_mode_id', 'destination_country_id')
    def _compute_port_of_discharge_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            if rec.destination_country_id:
                domain.append(('country_id', '=', rec.destination_country_id.id))
            rec.port_of_discharge_domain = json.dumps(domain)

    port_of_discharge_domain = fields.Char(compute='_compute_port_of_discharge_domain', store=True)

    @api.model
    def get_default_volume_uom(self):
        return self.env.company.volume_uom_id.id

    @api.model
    def _get_default_lead_stage(self):
        return self.env['crm.prospect.lead.stage'].search([], limit=1)

    def _compute_opportunity_count(self):
        for lead in self:
            lead.opportunity_count = self.env['crm.prospect.opportunity'].search_count([('lead_id', '=', lead.id)])

    name = fields.Char(string="Lead ID", required=True, copy=False, readonly=True, default=lambda self: "New Lead")
    date = fields.Date(required=True, default=lambda self: fields.Date.today())
    target_id = fields.Many2one('crm.sale.target')
    prospect_id = fields.Many2one('crm.prospect', required=True, string="Customer", tracking=True)
    street = fields.Char(string='Street', tracking=True)
    street2 = fields.Char(string='Street2', tracking=True)
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=', country_id)]", tracking=True)
    country_id = fields.Many2one('res.country', string='Country', tracking=True)
    city_id = fields.Many2one('res.city', string='City', domain="[('country_id', '=', country_id)]", tracking=True)
    zip = fields.Char(string="Zip Code", tracking=True)
    contact_name = fields.Char(string="Contact Person", tracking=True)
    designation = fields.Char(string="Designation", tracking=True)
    department = fields.Char(string="Department", tracking=True)
    email = fields.Char(string="Email", tracking=True)
    mobile = fields.Char(string="Mobile No", tracking=True)
    phone_no = fields.Char(string="Telephone No", tracking=True)
    user_id = fields.Many2one('res.users', string="Lead Owner", required=True, default=lambda self: self.env.user)
    lead_source = fields.Selection([
        ('db', 'Database'),
        ('social', 'Social'),
        ('customer_ref', 'Customer Reference'),
        ('trade_show', 'Trade Show'),
        ('inbound', 'Inbound')]
    )
    lead_source_id = fields.Many2one('lead.source', string='Lead Source', domain="[('allow_source_creation', '=', True)]")
    stage_id = fields.Many2one('crm.prospect.lead.stage', string="Lead Stage", default=_get_default_lead_stage, required=True, tracking=True)
    nature_of_business = fields.Char()
    company_turnover = fields.Monetary(currency_field='turnover_currency_id')
    turnover_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    remarks = fields.Text()
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    port_of_loading_id = fields.Many2one('freight.port', required=False, string="Origin Port/Airport")
    port_of_discharge_id = fields.Many2one('freight.port', required=False, string="Destination Port/Airport")
    transport_mode_id = fields.Many2one('transport.mode')
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    business_service_id = fields.Many2one('res.partner.industry', string="Business Service")
    expected_annual_revenue = fields.Monetary(currency_field='annual_revenue_currency_id', required=False)
    annual_revenue_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    expected_annual_volume = fields.Float()
    volume_uom_id = fields.Many2one('uom.uom', string="Volume UOM", domain=lambda self: [('category_id', '=', self.env.ref('uom.product_uom_categ_vol').id)], default=get_default_volume_uom)
    commodity_id = fields.Many2one('freight.commodity')
    target_date = fields.Date()
    shipment_type_id = fields.Many2one('shipment.type')
    lead_category = fields.Selection([
        ('hot', 'HOT'),
        ('warm', 'WARM'),
        ('cold', 'COLD')
    ])
    notes = fields.Text()
    is_create_opportunity = fields.Boolean(related='stage_id.is_create_opportunity', store=True)
    opportunity_count = fields.Integer(compute='_compute_opportunity_count')
    origin_country_id = fields.Many2one("res.country", string="Origin Country")
    destination_country_id = fields.Many2one("res.country", string="Destination Country")
    team_id = fields.Many2one('crm.prospect.team', 'Sales Team', ondelete="restrict", tracking=True,
                              check_company=True,
                              domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.model
    def create(self, vals):
        stages = [self.env.ref('crm_prospect_lead.crm_lead_stage_future_prospect').id,
                  self.env.ref('crm_prospect_lead.crm_lead_stage_closed').id,
                  self.env.ref('crm_prospect_lead.crm_lead_stage_disualified').id
                  ]
        lead = self.search([('stage_id', 'not in', stages), ('prospect_id', '=', vals.get('prospect_id')), ('user_id', '!=', vals.get('user_id'))], limit=1)
        if lead:
            raise ValidationError(_("Lead with same Customer is already exist with Lead Owner: %s", lead.user_id.name))
        return super().create(vals)

    @api.onchange('team_id')
    def onchange_team_id(self):
        if self.env.user not in self.team_id.member_ids:
            self.user_id = False
        elif self.env.user in self.team_id.member_ids or self.env.user in self.team_id.user_id:
            self.user_id = self.env.user.id
        return {'domain': {'user_id': [('id', 'in', self.team_id.member_ids.ids+self.team_id.user_id.ids)]}}

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.prospect_id.country_id.id != self.country_id.id:
            self.phone_no = ''
            self.mobile = ''
            if self.country_id != self.state_id.country_id:
                self.state_id = False
            if self.country_id != self.city_id.country_id:
                self.city_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id.id
        if self.city_id and self.city_id.state_id != self.state_id:
            self.city_id = False

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id.state_id:
            self.state_id = self.city_id.state_id.id
        if self.city_id.country_id:
            self.country_id = self.city_id.country_id.id
        self.zip = self.zip if self.zip else self.city_id.zipcode

    @api.onchange('prospect_id')
    def _onchange_prospect_id_field(self):
        mapping_column_dict = {
            'street': 'street1',
            'street2': 'street2',
            'country_id': 'country_id',
            'state_id': 'state_id',
            'city_id': 'city_id',
            'zip': 'zip',
            'contact_name': 'contact_name',
            'phone_no': 'phone_no',
            'designation': 'designation',
            'department': 'department',
            'email': 'email',
            'mobile': 'mobile'
        }
        values = {
            'street': False,
            'street2': False,
            'country_id': False,
            'state_id': False,
            'city_id': False,
            'zip': False,
            'contact_name': False,
            'phone_no': False,
            'designation': False,
            'department': False,
            'email': False,
            'mobile': False
        }
        if self.prospect_id:
            for key, value in mapping_column_dict.items():
                values[key] = self.prospect_id[value]
        self.update(values)

    def action_create_partner_address(self):
        self.ensure_one()
        PartnerObj = self.env['res.partner']
        prospect_partner = self.prospect_id.related_partner_id
        address = PartnerObj.search([
            ('street', '=', self.street),
            ('street2', '=', self.street2),
            ('email', '=', self.email),
            ('phone', '=', self.phone_no),
            ('mobile', '=', self.mobile),
            '|',
            ('id', '=', prospect_partner.id),
            ('parent_id', '=', prospect_partner.id),
        ], limit=1)
        if not address:
            PartnerObj.create({
                'parent_id': prospect_partner.id,
                'type': 'invoice',
                'street': self.street,
                'street2': self.street2,
                'email': self.email,
                'phone': self.phone_no,
                'mobile': self.mobile,
                'country_id': self.country_id.id
            })

    def action_create_get_partner(self):
        self.ensure_one()
        prospect_partner = self.prospect_id.related_partner_id
        if prospect_partner:
            self.action_create_partner_address()
            return prospect_partner
        vals = {
            'name': self.prospect_id.name,
            'street': self.prospect_id.street1,
            'street2': self.prospect_id.street2,
            'country_id': self.prospect_id.country_id.id,
            'city_id': self.prospect_id.city_id.id,
            'zip': self.prospect_id.zip,
            'phone': self.prospect_id.phone_no,
            'email': self.prospect_id.email,
            'mobile': self.prospect_id.mobile,
            'company_id': self.prospect_id.company_id.id,
            'category_ids': self.prospect_id.category_ids.ids,
        }
        partner = self.env['res.partner'].sudo().create(vals)
        self.prospect_id.related_partner_id = partner.id
        return partner

    def action_create_opportunity(self):
        self.ensure_one()
        partner = self.sudo().action_create_get_partner()
        context = self._context.copy()
        context.update({
            'default_date': self.date,
            'default_lead_id': self.id,
            'default_prospect_id': self.prospect_id.id,
            'default_transport_mode_id': self.transport_mode_id.id,
            'default_shipment_type_id': self.shipment_type_id.id,
            'default_commodity_id': self.commodity_id.id,
            'default_shipment_due_date': self.target_date,
            'default_port_of_loading_id': self.port_of_loading_id.id,
            'default_origin_country_id': self.origin_country_id and self.origin_country_id.id or self.port_of_loading_id.country_id.id,
            'default_port_of_discharge_id': self.port_of_discharge_id.id,
            'default_destination_country_id': self.destination_country_id and self.destination_country_id.id or self.port_of_discharge_id.country_id.id,
            'default_user_id': self.user_id.id,
            'default_company_id': self.company_id.id,
            'default_country_id': self.country_id.id,
            'default_state_id': self.state_id.id,
            'default_city_id': self.city_id.id,
            'default_zip': self.zip,
            # Contact details Lead to Opportunity/Prospect-Details Update
            'default_contact_name': self.contact_name,
            'default_email': self.email,
            'default_department': self.department,
            'default_designation': self.designation,
            'default_phone': self.phone_no,
            'default_mobile': self.mobile,
            'default_street1': self.street,
            'default_street2': self.street2,
            'default_is_create_from_lead': True,
            'default_customer_id': partner.id,
            'default_team_id': self.team_id.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.prospect.opportunity',
            'view_mode': 'form',
            'context': context,
        }

    def action_change_status(self):
        self.ensure_one()
        return {
            'name': 'Change Status',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.prospect.lead.status',
            'context': {'default_stage_id': self.stage_id.id,
                        'default_prospect_lead_id': self.id,
                        }
        }

    def action_open_opportunity(self):
        self.ensure_one()
        context = self._context.copy()
        context.update(default_lead_id=self.id)
        action = self.env['ir.actions.act_window']._for_xml_id('crm_prospect_lead.crm_prospect_opportunity_action')
        opportunity_ids = self.env['crm.prospect.opportunity'].search([('lead_id', '=', self.id)])
        if len(opportunity_ids) == 1:
            res = self.env.ref('crm_prospect_lead.crm_prospect_opportunity_view_form', False)
            form_view = [(res and res.id or False, 'form')]
            action.update({
                'view_mode': 'form',
                'views': form_view,
                'res_id': opportunity_ids.id,
                'context': context,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', opportunity_ids.ids)],
                'context': context,
            })
        return action

    @api.onchange('phone_no', 'country_id', 'company_id')
    def _onchange_phone_no_validation(self):
        if self.phone_no:
            self.phone_no = self._phone_format(self.phone_no)

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            self.mobile = self._phone_format(self.mobile)

    def _phone_format(self, number, country=None, company=None):
        country = country or self.country_id or self.env.company.country_id
        if not country:
            return number
        return phone_validation.phone_format(
            number,
            country.code if country else None,
            country.phone_code if country else None,
            force_format='INTERNATIONAL',
            raise_exception=False
        )

    @api.constrains('phone_no')
    def _check_phone_no(self):
        if self._context.get('skip_validation'):
            return {}
        for rec in self.filtered(lambda r: r.phone_no):
            try:
                phone_validation.phone_format(rec.phone_no, rec.country_id.code, rec.country_id.phone_code, force_format=False)
            except Exception:
                raise ValidationError(_('Please enter a valid phone number'))

    @api.constrains('mobile')
    def _check_mobile_no(self):
        if self._context.get('skip_validation'):
            return {}
        for rec in self.filtered(lambda r: r.mobile):
            try:
                phone_validation.phone_format(rec.mobile, rec.country_id.code, rec.country_id.phone_code, force_format=False)
            except Exception:
                raise ValidationError(_('Please enter a valid Mobile number'))

    @api.constrains('email')
    def validate_mail(self):
        if self.email:
            match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,5})$', str(self.email).lower())
            if not match:
                raise ValidationError('Not a valid E-mail ID')

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        values = {'port_of_loading_id': False, 'port_of_discharge_id': False, 'origin_country_id': False, 'destination_country_id': False}
        self.update(values)

    @api.constrains('port_of_loading_id', 'port_of_discharge_id')
    def _check_origin_destination_ports(self):
        for rec in self:
            if rec.port_of_loading_id and rec.port_of_discharge_id and rec.port_of_loading_id == rec.port_of_discharge_id:
                raise ValidationError(_('Origin and Destination Port/Airport Must be Different, It can not same.'))
