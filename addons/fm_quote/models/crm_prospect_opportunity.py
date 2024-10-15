# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError


class Opportunity(models.Model):
    _inherit = "crm.prospect.opportunity"

    allow_quote_creation = fields.Boolean(related='stage_id.allow_quote_creation')
    quotation_ids = fields.One2many('shipment.quote', 'opportunity_id')
    quotation_count = fields.Integer(compute='_compute_quotation_count')

    @api.constrains('port_of_loading_id', 'port_of_discharge_id', 'email')
    def _check_origin_destination_port_email(self):
        for rec in self:
            if rec.port_of_loading_id and rec.port_of_discharge_id and rec.port_of_loading_id == rec.port_of_discharge_id:
                raise ValidationError(_('Origin and Destination Port Must be Different, It can not same.'))
            if rec.email:
                match = tools.single_email_re.match(str(rec.email).lower())
                if not match:
                    raise ValidationError('Not a valid E-mail ID')

    def _compute_quotation_count(self):
        for opportunity in self:
            opportunity.quotation_count = len(opportunity.quotation_ids)

    def action_create_partner_address(self):
        self.ensure_one()
        PartnerObj = self.env['res.partner']
        prospect_partner = self.prospect_id.related_partner_id
        address = PartnerObj.search([
            ('street', '=', self.street1),
            ('street2', '=', self.street2),
            ('email', '=', self.email),
            ('phone', '=', self.phone),
            ('mobile', '=', self.mobile),
            '|',
            ('id', '=', prospect_partner.id),
            ('parent_id', '=', prospect_partner.id),
        ], limit=1)
        if not address:
            PartnerObj.create({
                'parent_id': prospect_partner.id,
                'type': 'invoice',
                'street': self.street1,
                'street2': self.street2,
                'email': self.email,
                'phone': self.phone,
                'mobile': self.mobile,
            })

    def action_create_get_partner(self):
        self.ensure_one()
        if self.opportunity_type == 'existing':
            return self.partner_id
        prospect_partner = self.prospect_id.related_partner_id
        if self.opportunity_type == 'new' and prospect_partner:
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
        }
        partner = self.env['res.partner'].sudo().create(vals)
        self.prospect_id.related_partner_id = partner.id
        return partner

    def _prepare_quotation_vals(self):
        self.ensure_one()
        partner = self.sudo().action_create_get_partner()
        quote_customer = self.customer_id
        address = quote_customer.get_default_addresses()
        shipper_id = False
        consignee_id = False
        agent_id = False
        shipper_address_id = False
        consignee_address_id = False
        agent_address_id = False
        if self.customer_type == 'consignor':
            shipper_id = partner.id
            shipper_address_id = address and address[0].id
        elif self.customer_type == 'consignee':
            consignee_id = partner.id
            consignee_address_id = address and address[0].id
        else:
            agent_id = partner.id
            agent_address_id = address and address[0].id

        quote_vals = {
            'from_opportunity': True,
            'default_date': self.date,
            'default_opportunity_id': self.id,
            'default_quote_expiry_date': self.shipment_due_date,
            'default_state': 'draft',
            'default_team_id': self.team_id.id,
            'default_user_id': self.user_id.id,
            'default_company_id': self.env.company.id,
            'default_client_id': quote_customer.id,
            'default_client_address_id': address and address[0].id,
            'default_shipper_id': shipper_id,
            'default_shipper_address_id': shipper_address_id,
            'default_consignee_id': consignee_id,
            'default_consignee_address_id': consignee_address_id,
            'default_agent_id': agent_id,
            'default_agent_address_id': agent_address_id,
            'default_transport_mode_id': self.transport_mode_id.id,
            'default_service_mode_id': self.service_mode_id.id,
            'default_shipment_type_id': self.shipment_type_id.id,
            'default_cargo_type_id': self.cargo_type_id.id,
            'default_incoterm_id': self.incoterm_id.id,
            'default_origin_country_id': self.origin_country_id.id,
            'default_origin_un_location_id': self.origin_un_location_id.id,
            'default_port_of_loading_id': self.port_of_loading_id.id,
            'default_destination_country_id': self.destination_country_id.id,
            'default_destination_un_location_id': self.destination_un_location_id.id,
            'default_port_of_discharge_id': self.port_of_discharge_id.id,
            'default_product_ids': [(6, 0, self.additional_service_ids.ids)],
            'default_quote_for': self.opportunity_for,
            'default_pickup_address': self.pickup_address,
            'default_delivery_address': self.delivery_address,
        }
        if not self.cargo_type_id.is_package_group:
            quote_vals['default_quote_container_line_ids'] = [(0, 0, {
                'container_type_id': container.container_type_id.id,
                'count': container.quantity
            }) for container in self.container_ids]
        else:
            quote_vals['default_quote_cargo_line_ids'] = [(0, 0, {
                'pack_type_id': package.package_uom_id.id,
                'weight_uom_id': package.weight_uom_id.id,
                'volume_uom_id': package.volume_uom_id.id,
                'weight': package.weight,
                'volume': package.volume,
                'count': package.quantity,
                'length': package.length,
                'width': package.width,
                'height': package.height,
                'lwh_uom_id': package.lwh_uom_id.id
            }) for package in self.package_ids]
        return quote_vals

    def action_create_quotation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'shipment.quote',
            'view_mode': 'form',
            'target': 'current',
            'context': self._prepare_quotation_vals()
        }

    def action_open_quotations(self):
        return {
            'name': _('Quotations'),
            'type': 'ir.actions.act_window',
            'res_model': 'shipment.quote',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', self.quotation_ids.ids)]
        }
