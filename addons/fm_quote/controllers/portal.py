# -*- coding: utf-8 -*-

import binascii

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.freight_base_portal.controllers import portal
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.mail import _message_post_helper


class QuotePortal(portal.FreightCustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(QuotePortal, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        shipment_quote = request.env['shipment.quote']
        if 'shipment_quote_count' in counters:
            values['shipment_quote_count'] = shipment_quote.search_count(self._prepare_shipment_quote_domain(partner)) \
                if shipment_quote.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_shipment_quote_domain(self, partner):
        return [('client_id', '=', partner.id), ('state', 'in', request.env['shipment.quote'].get_portal_visibility_state())]

    @http.route(['/my/shipment_quote', '/my/shipment_quote/page/<int:page>'], type='http', auth="user", website=True)
    def portal_shipment_quote(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        shipment_quotes = request.env['shipment.quote']
        domain = self._prepare_shipment_quote_domain(partner)
        shipment_quotes = shipment_quotes.search(domain)
        values.update({
            'shipment_quotes': shipment_quotes.sudo(),
            'page_name': 'shipment_quote',
            'default_url': '/my/shipment_quote',
        })
        return request.render("fm_quote.portal_my_shipment_quote", values)

    @http.route(['/my/shipment_quote/<int:shipment_quote_id>'], type='http', auth="public", website=True)
    def portal_shipment_quote_page(self, shipment_quote_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            shipment_quote_sudo = self._document_check_access('shipment.quote', shipment_quote_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

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
                'landing_route': '/shop/payment/validate',
                'bootstrap_formatting': True,
                'partner_id': shipment_quote_sudo.client_id.id,
                'report_type': 'html',
                'action': shipment_quote_sudo._get_portal_return_action(),
                'reject_reason': reject_reason_ids,
            }
            if shipment_quote_sudo.company_id:
                values['res_company'] = shipment_quote_sudo.company_id
            return request.render('fm_quote.shipment_quote_portal_template', values)

    @http.route(['/my/shipment_quote/<int:shipment_quote_id>/accept'], type='json', auth="public", website=True)
    def portal_shipment_quote_accept(self, shipment_quote_id, access_token=None, name=None, signature=None):
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
        shipment_quote_sudo._send_order_confirmation_mail()

        query_string = '&message=sign_ok'
        return {
            'force_refresh': True,
            'redirect_url': shipment_quote_sudo.get_portal_url(query_string=query_string),
        }

    @http.route(['/my/shipment_quote/<int:shipment_quote_id>/decline'], type='http', auth="public", methods=['POST'], website=True)
    def portal_shipment_quote_decline(self, shipment_quote_id, access_token=None, **post):
        try:
            shipment_quote_sudo = self._document_check_access('shipment.quote', shipment_quote_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        decline_message = post.get('decline_message')
        query_string = False
        if shipment_quote_sudo:
            shipment_quote_sudo.action_reject()
            if decline_message:
                shipment_quote_sudo.write({
                    'decline_message': decline_message,
                })
                shipment_quote_sudo._send_quote_rejection_mail()
        else:
            query_string = "&message=cant_reject"

        return request.redirect(shipment_quote_sudo.get_portal_url(query_string=query_string))
