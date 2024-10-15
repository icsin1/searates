# -*- coding: utf-8 -*-

import binascii

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.freight_base_portal.controllers import portal
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.mail import _message_post_helper


class ProFormaInvoicePortal(portal.FreightCustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(ProFormaInvoicePortal, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        pro_forma_invoice_obj = request.env['pro.forma.invoice']
        if 'pro_forma_invoice_count' in counters:
            values['pro_forma_invoice_count'] = pro_forma_invoice_obj.search_count(self._prepare_pro_forma_invoice_domain(partner)) \
                if pro_forma_invoice_obj.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_pro_forma_invoice_domain(self, partner):
        return [('partner_id', '=', partner.id)]

    @http.route(['/my/pro_forma_invoice', '/my/pro_forma_invoice/page/<int:page>'], type='http', auth="user", website=True)
    def portal_pro_forma_invoice(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        pro_forma_invoice_obj = request.env['pro.forma.invoice']
        domain = self._prepare_pro_forma_invoice_domain(partner)
        pro_forma_invoice_ids = pro_forma_invoice_obj.search(domain)
        values.update({
            'pro_forma_invoice_ids': pro_forma_invoice_ids.sudo(),
            'page_name': 'pro_forma_invoice',
            'default_url': '/my/pro_forma_invoice',
        })
        return request.render("fm_proforma.portal_my_pro_forma_invoice", values)

    @http.route(['/my/pro_forma_invoice/<int:pro_forma_invoice_id>'], type='http', auth="public", website=True)
    def portal_pro_forma_invoice_page(self, pro_forma_invoice_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            pro_forma_invoice_sudo = self._document_check_access('pro.forma.invoice', pro_forma_invoice_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text', 'docx'):
            return self._generate_document_report(record=pro_forma_invoice_sudo, report_type=report_type, report_ref='fm_proforma.doc_type_proforma_invoice', download=download)

        if pro_forma_invoice_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_pro_forma_invoice_%s' % pro_forma_invoice_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_pro_forma_invoice_%s' % pro_forma_invoice_sudo.id] = now
                body = _('Pro Forma Invoice viewed by customer %s', pro_forma_invoice_sudo.partner_id.name)
                _message_post_helper(
                    "pro.forma.invoice",
                    pro_forma_invoice_sudo.id,
                    body,
                    token=pro_forma_invoice_sudo.access_token,
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=pro_forma_invoice_sudo.create_uid.sudo().partner_id.ids,
                )
            values = {
                'pro_forma_invoice': pro_forma_invoice_sudo,
                'message': message,
                'token': access_token,
                'bootstrap_formatting': True,
                'partner_id': pro_forma_invoice_sudo.partner_id.id,
                'report_type': 'html',
                'action': pro_forma_invoice_sudo._get_portal_return_action(),
            }
            if pro_forma_invoice_sudo.company_id:
                values['res_company'] = pro_forma_invoice_sudo.company_id
            return request.render('fm_proforma.pro_forma_invoice_portal_template', values)

    @http.route(['/my/pro_forma_invoice/<int:pro_forma_invoice_id>/accept'], type='json', auth="public", website=True)
    def portal_pro_forma_invoice_accept(self, pro_forma_invoice_id, access_token=None, name=None, signature=None):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            pro_forma_invoice_sudo = self._document_check_access('pro.forma.invoice', pro_forma_invoice_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid Pro Forma Invoice.')}

        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            pro_forma_invoice_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'image_1920': signature
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error):
            return {'error': _('Invalid signature data.')}

        pro_forma_invoice_sudo.action_approve_pro_forma()
        pro_forma_invoice_sudo._send_pro_forma_confirmation_mail()

        query_string = '&message=sign_ok'
        return {
            'force_refresh': True,
            'redirect_url': pro_forma_invoice_sudo.get_portal_url(query_string=query_string),
        }

    @http.route(['/my/pro_forma_invoice/<int:pro_forma_invoice_id>/decline'], type='http', auth="public", methods=['POST'], website=True)
    def portal_pro_forma_invoice_decline(self, pro_forma_invoice_id, access_token=None, **post):
        try:
            pro_forma_invoice_sudo = self._document_check_access('pro.forma.invoice', pro_forma_invoice_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        decline_message = post.get('decline_message')
        query_string = False
        if pro_forma_invoice_sudo:
            pro_forma_invoice_sudo.action_cancel_pro_forma()
            if decline_message:
                pro_forma_invoice_sudo.write({
                    'reject_reason': decline_message,
                })
                pro_forma_invoice_sudo._send_pro_forma_reject_mail()
        else:
            query_string = "&message=cant_reject"
        return request.redirect(pro_forma_invoice_sudo.get_portal_url(query_string=query_string))
