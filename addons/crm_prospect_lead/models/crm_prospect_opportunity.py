# -*- coding: utf-8 -*-
import json
import re
from odoo import api, models, fields, _
from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import ValidationError


class Opportunity(models.Model):
    _name = "crm.prospect.opportunity"
    _description = "Prospect Opportunity"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_default_stage(self):
        return self.env['crm.prospect.opportunity.stage'].search([], limit=1)

    def get_loading_port_domain(self):
        self.ensure_one()
        domain = []
        if self.origin_country_id:
            domain.append(('country_id', '=', self.origin_country_id.id))
        if self.transport_mode_id:
            domain.append(('transport_mode_id', '=', self.transport_mode_id.id))
        return json.dumps(domain)

    def get_discharge_port_domain(self):
        self.ensure_one()
        domain = []
        if self.destination_country_id:
            domain.append(('country_id', '=', self.destination_country_id.id))
        if self.transport_mode_id:
            domain.append(('transport_mode_id', '=', self.transport_mode_id.id))
        return json.dumps(domain)

    @api.onchange('opportunity_for')
    def _onchange_opportunity_for(self):
        if self.opportunity_for == 'job':
            self.update({
                'transport_mode_id': False,
                'shipment_type_id': False,
                'cargo_type_id': False,
            })

    @api.depends('opportunity_for', 'origin_country_id', 'transport_mode_id')
    def _compute_loading_port_domain(self):
        for opportunity in self:
            opportunity.loading_port_domain = opportunity.get_loading_port_domain()

    @api.depends('opportunity_for', 'destination_country_id', 'transport_mode_id')
    def _compute_discharge_port_domain(self):
        for opportunity in self:
            opportunity.discharge_port_domain = opportunity.get_discharge_port_domain()

    @api.depends('transport_mode_id')
    def _compute_cargo_type_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.cargo_type_domain = json.dumps(domain)

    cargo_type_domain = fields.Char(compute='_compute_cargo_type_domain', store=True)

    name = fields.Char(string='Opportunity Number', required=True, copy=False, readonly=True, index=True, default=lambda self: "New Opportunity")
    date = fields.Date(required=True, default=lambda self: fields.Date.today())
    location_id = fields.Many2one("freight.un.location")
    lead_id = fields.Many2one("crm.prospect.lead")
    opportunity_type = fields.Selection([
        ("new", "New Client"),
        ("existing", "Existing Client")
    ], default="new")
    opportunity_for = fields.Selection([
        ('shipment', 'Shipment'),
    ], default='shipment', string="Type")
    opportunity_source = fields.Selection([
        ("online", "Online"),
        ("offline", "Offline")
    ], default="online")
    user_id = fields.Many2one("res.users", string="Sales Agent", required=True,
                              default=lambda self: self.env.user, tracking=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    stage_id = fields.Many2one("crm.prospect.opportunity.stage", string="Opportunity Stage",
                               default=_get_default_stage, required=True, tracking=True)
    # Party Details
    customer_type = fields.Selection([
        ("consignor", "Shipper"),
        ("consignee", "Consignee"),
        ("agent", 'Agent')
    ], default="consignor")
    prospect_id = fields.Many2one("crm.prospect", string="Prospect", tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    street1 = fields.Char()
    street2 = fields.Char()
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=', country_id)]")
    city_id = fields.Many2one('res.city', string='City', domain="[('country_id', '=', country_id)]")
    country_id = fields.Many2one('res.country', string='Country')
    zip = fields.Char(string="Zip Code")
    contact_name = fields.Char("Contact Person")
    designation = fields.Char()
    department = fields.Char()
    email = fields.Char()
    mobile = fields.Char("Mobile No")
    phone = fields.Char("Telephone No")
    # Shipment Details
    commodity_id = fields.Many2one("freight.commodity", string="Commodity")
    cargo_description = fields.Text()
    cargo_status = fields.Selection([
        ("ready", "Ready to Ship"),
        ("later", "Ship Later"),
    ], default="ready")
    shipment_due_date = fields.Date("Estimated Shipment Date")
    transport_mode_id = fields.Many2one("transport.mode", string="Transport Mode")
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True)
    shipment_type_id = fields.Many2one("shipment.type", string="Shipment Type")
    incoterm_id = fields.Many2one("account.incoterms", string="Incoterms")
    service_mode_id = fields.Many2one("freight.service.mode", string="Service Mode")
    additional_service_ids = fields.Many2many("product.product", string="Additional Services", domain=lambda self: [('categ_id', '=', self.env.ref('freight_base.shipment_other_charge_category').id)])

    origin_country_id = fields.Many2one("res.country", string="Origin/Pickup Country")
    origin_un_location_id = fields.Many2one("freight.un.location", string="Origin", domain="[('country_id', '=', origin_country_id)]")
    port_of_loading_id = fields.Many2one("freight.port", string="Origin Port/AirPort")
    loading_port_domain = fields.Char(compute='_compute_loading_port_domain')

    destination_country_id = fields.Many2one("res.country", string="Destination/Delivery Country")
    destination_un_location_id = fields.Many2one("freight.un.location", string="Destination", domain="[('country_id', '=', destination_country_id)]")
    port_of_discharge_id = fields.Many2one("freight.port", string="Destination Port/AirPort", domain="[('country_id', '=', destination_country_id),('transport_mode_id', '=', transport_mode_id)]")
    discharge_port_domain = fields.Char(compute='_compute_discharge_port_domain')

    cargo_type_id = fields.Many2one("cargo.type", string="Cargo Type")
    # Package Details
    package_ids = fields.One2many("crm.prospect.opportunity.package", "opportunity_id", string="Packages")
    # Container Details
    container_ids = fields.One2many("crm.prospect.opportunity.container", "opportunity_id", string="Containers")
    is_package_group = fields.Boolean(related="cargo_type_id.is_package_group")
    is_create_from_lead = fields.Boolean('Is create from lead', default=False)
    # team
    team_id = fields.Many2one(
        'crm.prospect.team', 'Sales Team',
        ondelete="restrict", tracking=True,
        check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    pricing_team_id = fields.Many2one("res.users", string="Pricing Team", tracking=True)
    customer_id = fields.Many2one('res.partner', domain="[('type', '=', 'contact'), '|', ('company_id', '=', False), "
                                  "('company_id', '=', company_id)]", string='Customer',
                                  tracking=True)
    agent_id = fields.Many2one('res.partner', domain=lambda self: [('category_ids', 'in', self.env.ref('freight_base.org_type_agent').ids),
                                                                   ('freight_carrier_id', '!=', False)], string='Shipping Provider')
    rate_count = fields.Integer(compute='_compute_rate_count')
    # Address Fields
    pickup_address = fields.Text('Pickup Address')
    delivery_address = fields.Text('Delivery Address')
    incoterm_check = fields.Boolean(related='incoterm_id.incoterm_check')
    opp_check = fields.Boolean('Opp Check', compute='_compute_opp_check')
    customer_visit_ids = fields.One2many('customer.visit.lines', 'opportunity_id', string="Customer Visit Information")

    @api.depends('company_id')
    def _compute_opp_check(self):
        is_opp_check = self.env['ir.config_parameter'].sudo().get_param('freight_management.enable_non_mandatory_fields')
        for rec in self:
            if is_opp_check:
                rec.opp_check = True
            else:
                rec.opp_check = False

    def _create_rate_request_vals(self):
        self.ensure_one()
        rate_vals = {}
        RateRequestObj = self.env['rate.request']
        rate_number = self.env['ir.sequence'].next_by_code('rate.request.code') or _('New')
        if self.agent_id:
            rate_vals = {
                'name': rate_number,
                'agent_id': self.agent_id.id,
                'opportunity_id': self.id
            }
        return RateRequestObj.create(rate_vals)

    def action_rate_request(self):
        self.ensure_one()
        if not self.agent_id:
            raise ValidationError(_("For The Rate Request, Shipping Provider Must Be Selected!"))
        template_id = self.env['ir.model.data']._xmlid_to_res_id('crm_prospect_lead.opportunity_rate_request_email_template', raise_if_not_found=False)
        ctx = {
            'default_model': self._name,
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_light",
            'is_rate_request': True,
        }
        return {
            'name': 'Quote: Mail Composer',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _message_subscribe(self, partner_ids=None, subtype_ids=None, customer_ids=None):
        """
            Override the _message_subscribe method to prevent sending emails to
            external users when cron job runs.This is because external users are not part of the company's user
            list and therefore should not receive emails.
        """
        if self.env.context.get('fetchmail_cron_running'):
            partner_ids = self.env['res.partner'].browse(partner_ids)
            partner_ids = partner_ids.filtered(lambda partner: partner.user_ids - partner.user_ids.filtered('share')).ids
        return super()._message_subscribe(partner_ids, subtype_ids, customer_ids)

    def _compute_rate_count(self):
        for rate in self:
            count = self.env['rate.request'].search_count([('opportunity_id', '=', self.id)])
            rate.rate_count = count

    def action_open_rate_requests(self):
        return {
            'name': _('Rate Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'rate.request',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [('opportunity_id', '=', self.id)],
        }

    @api.onchange('team_id')
    def onchange_team_id(self):
        if self.env.user not in self.team_id.member_ids:
            self.user_id = False
        elif self.env.user in self.team_id.member_ids or self.env.user in self.team_id.user_id:
            self.user_id = self.env.user.id
        return {'domain': {'user_id': [('id', 'in', self.team_id.member_ids.ids + self.team_id.user_id.ids)]}}

    @api.onchange('partner_id', 'prospect_id', 'opportunity_type')
    def _onchange_partner_id(self):
        """The method override for resetting the Customer-type values"""
        for rec in self:
            rec.street1 = rec.partner_id.street if rec.opportunity_type == 'existing' and rec.partner_id else None or rec.prospect_id.street1 if rec.opportunity_type == 'new' and rec.prospect_id else None
            rec.street2 = rec.partner_id.street2 if rec.opportunity_type == 'existing' and rec.partner_id else None or rec.prospect_id.street2 if rec.opportunity_type == 'new' and rec.prospect_id else None
            rec.country_id = rec.partner_id.country_id if rec.opportunity_type == 'existing' and rec.partner_id else None or rec.prospect_id.country_id if rec.opportunity_type == 'new' and rec.prospect_id else None
            rec.state_id = rec.partner_id.state_id if rec.opportunity_type == 'existing' and rec.partner_id else None or rec.prospect_id.state_id if rec.opportunity_type == 'new' and rec.prospect_id else None
            rec.city_id = rec.partner_id.city_id if rec.opportunity_type == 'existing' and rec.partner_id else None or rec.prospect_id.city_id if rec.opportunity_type == 'new' and rec.prospect_id else None
            rec.zip = rec.partner_id.zip if rec.opportunity_type == 'existing' and rec.partner_id else None or rec.prospect_id.zip if rec.opportunity_type == 'new' and rec.prospect_id else None
            rec.email = rec.partner_id.email if rec.opportunity_type == 'existing' and rec.partner_id else None or rec.prospect_id.email if rec.opportunity_type == 'new' and rec.prospect_id else None
            rec.mobile = rec.partner_id.mobile if rec.opportunity_type == 'existing' and rec.partner_id else None or rec.prospect_id.mobile if rec.opportunity_type == 'new' and rec.prospect_id else None
            rec.phone = rec.partner_id.phone if rec.opportunity_type == 'existing' and rec.partner_id else None or rec.prospect_id.phone_no if rec.opportunity_type == 'new' and rec.prospect_id else None
            rec.contact_name = rec.opportunity_type == 'existing' and rec.partner_id and rec.partner_id.contact_person or rec.prospect_id.contact_name
            rec.designation = rec.opportunity_type == 'new' and rec.prospect_id and rec.prospect_id.designation or ''
            rec.department = rec.opportunity_type == 'new' and rec.prospect_id and rec.prospect_id.department or ''
            if rec.opportunity_type == 'existing':
                rec.prospect_id = False
            elif rec.opportunity_type == 'new':
                rec.partner_id = False
            user_id = False
            if rec.opportunity_type == 'existing' and rec.partner_id and rec.partner_id.user_id:
                user_id = rec.partner_id.user_id.id
            if rec.opportunity_type == 'new' and rec.prospect_id and rec.prospect_id.related_partner_id.user_id:
                user_id = rec.prospect_id.related_partner_id.user_id.id
            rec.user_id = user_id or self.env.user.id

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            if (self.prospect_id and self.prospect_id.country_id != self.country_id) or (self.partner_id and self.partner_id.country_id != self.country_id):
                self.phone = ''
                self.mobile = ''
            if self.country_id != self.state_id.country_id:
                self.state_id = False
            if self.country_id != self.city_id.country_id:
                self.city_id = False

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        record = super(Opportunity, self).copy(default)
        record.lead_id = False
        return record

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

    @api.constrains('email')
    def validate_mail(self):
        if self.email:
            match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,5})$', str(self.email).lower())
            if not match:
                raise ValidationError('Not a valid E-mail ID')

    def action_change_status(self):
        self.ensure_one()
        context = self._context.copy()
        context.update({
            'default_prospect_opportunity_id': self.id,
            'default_stage_id': self.stage_id.id
        })
        return {
            'name': 'Change Status',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.prospect.opportunity.status',
            'context': context,
        }

    @api.onchange('origin_country_id')
    def _onchange_origin_country_id(self):
        values = {'origin_un_location_id': False}
        if (self.lead_id and self.lead_id.port_of_loading_id.country_id.id != self.origin_country_id.id) or not self.lead_id:
            values.update({
                'port_of_loading_id': False,
            })
        else:
            values.update({
                'port_of_loading_id': self.lead_id.port_of_loading_id.id,
            })
        self.update(values)

    @api.onchange('destination_country_id')
    def _onchange_destination_country_id(self):
        values = {}
        if (self.lead_id and self.lead_id.port_of_discharge_id.country_id.id != self.destination_country_id.id) or not self.lead_id:
            values.update({
                'port_of_discharge_id': False,
            })
        else:
            values.update({
                'port_of_discharge_id': self.lead_id.port_of_discharge_id.id,
            })
        self.update(values)

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = self._phone_format(self.phone)

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

    @api.constrains('phone')
    def _check_phone_no(self):
        for rec in self.filtered(lambda r: r.phone):
            try:
                phone_validation.phone_format(rec.phone, rec.country_id.code, rec.country_id.phone_code, force_format=False)
            except Exception:
                raise ValidationError('Please enter a valid phone number')

    @api.constrains('mobile')
    def _check_mobile_no(self):
        for rec in self.filtered(lambda r: r.mobile):
            try:
                phone_validation.phone_format(rec.mobile, rec.country_id.code, rec.country_id.phone_code, force_format=False)
            except Exception:
                raise ValidationError(_('Please enter a valid Mobile number'))

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        values = {}
        if self.lead_id and self.lead_id.transport_mode_id.id != self.transport_mode_id.id or not self.lead_id:
            values.update({'port_of_loading_id': False, 'port_of_discharge_id': False, 'cargo_type_id': False})
        else:
            values.update({'port_of_loading_id': self.lead_id.port_of_loading_id.id,
                           'port_of_discharge_id': self.lead_id.port_of_discharge_id.id,
                           })
        self.update(values)
