# -*- coding: utf-8 -*-

import binascii
from collections import OrderedDict

from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.fm_quote.controllers.portal import QuotePortal
from odoo.addons.portal.controllers.mail import _message_post_helper


class QuoteDashboardPortal(QuotePortal):
    MANDATORY_SHIPMENT_QUOTE_FIELDS = ["name", "transport_mode_id", "email", "shipment_type_id", "cargo_type_id", "origin_country_id", "origin_id", "destination_country_id", "destination_id"]

    _items_per_page = 10

    def _prepare_home_portal_values(self, counters):
        values = super(QuoteDashboardPortal, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        shipment_quote = request.env['shipment.quote']
        if 'approved_shipment_quote_count' in counters:
            values['approved_shipment_quote_count'] = shipment_quote.search_count(
                self._prepare_approved_shipment_quote_domain(partner)) \
                if shipment_quote.check_access_rights('read', raise_exception=False) else 0
        if 'approved_shipment_un_accepted_quote_count' in counters:
            values['approved_shipment_un_accepted_quote_count'] = shipment_quote.search_count([
                ('client_id', '=', partner.id),
                ('state', 'in', ('approved', 'sent'))
            ]) if shipment_quote.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_approved_shipment_quote_domain(self, partner):
        return [
            ('client_id', '=', partner.id),
            ('state', '=', 'accept')
        ]

    @http.route(['/dashboard/shipment_quotes', '/dashboard/shipment_quotes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_menu_shipment_quotes(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        shipment_quote = request.env['shipment.quote']
        domain = [('client_id', '=', partner.id)]

        searchbar_filters = {
            'accepted': {'label': _('Accepted'), 'domain': [('state', '=', 'accept')]},
            'unaccepted': {'label': _('Un-Accepted'), 'domain': [('state', 'in', ('approved', 'sent'))]},
            'rejected': {'label': _('Rejected'), 'domain': [('state', 'in', ('expire', 'cancel', 'reject'))]},
        }
        # default filter by value
        if not filterby:
            filterby = 'accepted'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quote_count = shipment_quote.search_count(domain)
        # pager
        pager = portal_pager(
            url="/dashboard/shipment_quotes",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=quote_count,
            page=page,
            step=self._items_per_page
        )

        # search the count to display, according to the pager data
        quotes = shipment_quote.search(domain, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quote_history'] = quotes.ids[:100]

        values.update({
            'date': date_begin,
            'shipment_quotes': quotes.sudo(),
            'page_name': 'quote_menu',
            'pager': pager,
            'default_url': '/dashboard/shipment_quotes',
            'searchbar_filters': OrderedDict(searchbar_filters.items()),
            'filterby': filterby,
        })
        return request.render("ics_customer_portal_quote.portal_dashboard_shipment_quote", values)

    @http.route(['/dashboard/shipment_quote/<int:shipment_quote_id>'], type='http', auth="public", website=True)
    def portal_shipment_quote_view(self, shipment_quote_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            shipment_quote_sudo = self._document_check_access('shipment.quote', shipment_quote_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/dashboard')

        if report_type in ('html', 'pdf', 'text', 'docx'):
            return self._generate_document_report(record=shipment_quote_sudo, report_type=report_type, report_ref='fm_quote.doc_type_quote_quotation', download=download)

        if shipment_quote_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_shipment_quote_%s' % shipment_quote_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_shipment_quote_%s' % shipment_quote_sudo.id] = now
                body = _('Shipment quote viewed by customer %s', shipment_quote_sudo.client_id.name)
                _message_post_helper(
                    "shipment.quote",
                    shipment_quote_sudo.id,
                    body,
                    token=shipment_quote_sudo.access_token,
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=shipment_quote_sudo.user_id.sudo().partner_id.ids,
                )
            reject_reason_ids = request.env['change.reason'].sudo().search([])
            values = {
                'shipment_quote': shipment_quote_sudo,
                'message': message,
                'token': access_token,
                'landing_route': '/dashboard',
                'bootstrap_formatting': True,
                'partner_id': shipment_quote_sudo.client_id.id,
                'report_type': 'html',
                'page_name': 'quote_menu',
                'action': shipment_quote_sudo._get_portal_return_action(),
                'reject_reason': reject_reason_ids,
            }
            if shipment_quote_sudo.company_id:
                values['res_company'] = shipment_quote_sudo.company_id
            return request.render('ics_customer_portal_quote.shipment_quote_portal_view_template', values)

    @http.route(['/dashboard/shipment_quote/<int:shipment_quote_id>/accept'], type='json', auth="public", website=True)
    def portal_shipment_quote_view_accept(self, shipment_quote_id, access_token=None, name=None, signature=None):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            shipment_quote_sudo = self._document_check_access('shipment.quote', shipment_quote_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}

        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            shipment_quote_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'image_1920': signature,
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error):
            return {'error': _('Invalid signature data.')}

        shipment_quote_sudo.action_accept()
        shipment_quote_sudo.with_context(force_send=False)._send_order_confirmation_mail()

        query_string = '&message=sign_ok'
        return {
            'force_refresh': True,
            'redirect_url': shipment_quote_sudo.get_portal_url(query_string=query_string),
        }

    @http.route(['/dashboard/shipment_quote/<int:shipment_quote_id>/decline'], type='http', auth="public", methods=['POST'], website=True)
    def portal_shipment_quote_view_decline(self, shipment_quote_id, access_token=None, **post):
        try:
            shipment_quote_sudo = self._document_check_access('shipment.quote', shipment_quote_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/dashboard')

        decline_message = post.get('decline_message')
        query_string = False
        if shipment_quote_sudo:
            shipment_quote_sudo.action_reject()
            if decline_message:
                shipment_quote_sudo.write({
                    'decline_message': decline_message,
                })
                shipment_quote_sudo.with_context(force_send=False)._send_quote_rejection_mail()
        else:
            query_string = "&message=cant_reject"

        return request.redirect(shipment_quote_sudo.get_portal_url(query_string=query_string))

    def request_quote_details_form_mandatory_field_validate(self, data):
        error = dict()
        error_message = []
        # Validation
        for field_name in self.MANDATORY_SHIPMENT_QUOTE_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'
        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))
        return error, error_message

    def request_quote_details_form_field_validate(self, data):
        error = dict()
        error_message = []

        if data.get("origin_port_id") and data.get("destination_port_id") and int(
                data.get("origin_port_id")) == int(data.get("destination_port_id")):
            error["destination_port_id"] = 'error'
            error["origin_port_id"] = 'error'
            error_message.append(_('Origin and Destination Port Must be Different, It can not same.'))

        return error, error_message

    def create_data_record_vals_for_request_quote(self, data, partner):
        vals = {
            'client_id': partner.id,
            'date': data.get("date"),
            'shipper_id': int(data.get("shipper_id")) if data.get("shipper_id", False) else False,
            'consignee_id': int(data.get("consignee_id")) if data.get("consignee_id", False) else False,
            'transport_mode_id': int(data.get("transport_mode_id")) if data.get("transport_mode_id",
                                                                                False) else False,
            'shipment_type_id': int(data.get("shipment_type_id")) if data.get("shipment_type_id", False) else False,
            'cargo_type_id': int(data.get("cargo_type_id")) if data.get("cargo_type_id", False) else False,
            'incoterm_id': int(data.get("incoterm_id")) if data.get("incoterm_id", False) else False,
            'port_of_loading_id': int(data.get("origin_port_id")) if data.get("origin_port_id", False) else False,
            'port_of_discharge_id': int(data.get("destination_port_id")) if data.get("destination_port_id",
                                                                                     False) else False,
            'origin_country_id': int(data.get("origin_country_id")) if data.get("origin_country_id",
                                                                                False) else False,
            'origin_un_location_id': int(data.get("origin_id")) if data.get("origin_id", False) else False,
            'destination_country_id': int(data.get("destination_country_id")) if data.get("destination_country_id",
                                                                                          False) else False,
            'destination_un_location_id': int(data.get("destination_id")) if data.get("destination_id",
                                                                                      False) else False,
            'generated_from_portal': True,
            'quote_for': 'shipment',
            'approving_user_id': request.env.user.company_id.quote_approver_id.id if request.env.user.company_id.quote_approver_id else False,
            'user_id': request.env.user.company_id.quote_sale_agent_id.id if request.env.user.company_id.quote_sale_agent_id else False,
        }

        return vals

    def get_client_address(self, partner):

        partner_address = partner.get_default_addresses()
        client_address = ""
        if partner_address:
            if partner_address.street:
                client_address += partner_address.street + ","
            if partner_address.street2:
                client_address += partner_address.street2 + ","
            if partner_address.city:
                client_address += partner_address.city + ","
            if partner_address.state_id:
                client_address += partner_address.state_id.name + ","
            if partner_address.country_id:
                client_address += partner_address.country_id.name

        return client_address

    def get_shipment_quote_form_selection_fields_data_value(self):
        fields_data_dict = {}
        shipper = request.env['res.partner'].sudo().search([('type', '=', 'contact')])
        consignee = request.env['res.partner'].sudo().search([('type', '=', 'contact')])
        transport_mode = request.env['transport.mode'].sudo().search([])
        shipment_type = request.env['shipment.type'].sudo().search([('is_courier_shipment', '=', False)])
        cargo_type = request.env['cargo.type'].sudo().search([('is_courier_shipment', '=', False)])
        incoterm = request.env['account.incoterms'].sudo().search([])
        origin_port = request.env['freight.port'].sudo().search([])
        destination_port = request.env['freight.port'].sudo().search([])
        origin_country = request.env['res.country'].sudo().search([])
        destination_country = request.env['res.country'].sudo().search([])

        fields_data_dict.update({
            'shippers': shipper,
            'consignees': consignee,
            'transport_modes': transport_mode,
            'shipment_types': shipment_type,
            'cargo_types': cargo_type,
            'incoterms': incoterm,
            'origin_ports': origin_port,
            'destination_ports': destination_port,
            'origin_countrys': origin_country,
            'origins': [],
            'destination_countrys': destination_country,
            'destinations': [],
            'page_name': "my_request_quote",
        })
        return fields_data_dict

    @http.route(['/dashboard/request_quote'], type='http', auth="user", website=True)
    def portal_request_quote(self, redirect=None, **post):
        values = {}
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':

            error, error_message = self.request_quote_details_form_mandatory_field_validate(post)
            values.update({'error': error, 'error_message': error_message})

            error, error_message = self.request_quote_details_form_field_validate(post)
            values.update({'error': error, 'error_message': error_message})

            values.update(post)

            if not error:
                data_record = self.create_data_record_vals_for_request_quote(post, partner)
                if not data_record.get('approving_user_id') or not data_record.get('user_id'):
                    val = {
                        'page_name': 'quote_request_menu',
                    }
                    return request.render('ics_customer_portal_quote.quote_error_msg_template', val)

                else:
                    shipment_quote = request.env['shipment.quote'].sudo().create(data_record)
                    val = {
                        'name': shipment_quote.name,
                        'page_name': 'quote_request_menu',
                    }
                    return request.render('ics_customer_portal_quote.quote_thank_you_template', val)

        fields_data = self.get_shipment_quote_form_selection_fields_data_value()

        client_address = self.get_client_address(partner)
        fields_data.update({
            'page_name': 'quote_request_menu',
        })
        values.update({
            'partner': partner,
            'partner_address': client_address,
        })
        values.update(fields_data)
        response = request.render("ics_customer_portal_quote.portal_my_request_quote", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route(['/fetch_un_locations_based_on_country'], type='json', auth="user", website=True)
    def fetch_un_locations_based_on_country(self, redirect=None, **post):
        country_id = post.get('country_id', False)
        location_mode = post.get('location_mode', '')
        try:
            country_id = int(country_id)
        except Exception:
            country_id = ''
        un_locations = request.env['freight.un.location']
        selection_options = ''
        if country_id:
            un_location_ids = un_locations.sudo().search([('country_id', '=', country_id)])
            if un_location_ids:
                selection_options = "<option value="">Select %s...</option>" % (location_mode)
                for location in un_location_ids:
                    selection_options += '<option value=%s>%s</option>' % (str(location.id), location.name)
        return selection_options
