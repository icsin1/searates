# -*- coding: utf-8 -*-

import base64
import os
from collections import OrderedDict
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import pager as portal_pager


class ServiceJobsShipmentPortal(portal.CustomerPortal):

    _items_per_page = 10

    def _prepare_home_portal_values(self, counters):
        """
        Add Service jobs shipment counts
        """
        values = super()._prepare_home_portal_values(counters)
        freight_shipment = request.env['freight.service.job']
        if 'service_jobs_shipment_count' in counters:
            values['service_jobs_shipment_count'] = freight_shipment.search_count(self._prepare_shipment_service_jobs_domain()) \
                if freight_shipment.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_shipment_service_jobs_domain(self):
        return [
            ('state', 'in', ['created', 'cancelled', 'completed']),
            ('client_id', '=', request.env.user.partner_id.id)
        ]

    @http.route(['/dashboard/service_jobs_shipment', '/dashboard/service_jobs_shipment/page/<int:page>'], type='http', auth="user", website=True)
    def portal_service_jobs_shipment(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        freight_shipment = request.env['freight.service.job']
        domain = self._prepare_shipment_service_jobs_domain()

        searchbar_filters = {
            'created': {'label': _('Created'), 'domain': [("state", "=", 'created')]},
            'completed': {'label': _('Completed'), 'domain': [("state", "=", 'completed')]},
            'cancelled': {'label': _('Cancelled'), 'domain': [("state", "=", 'cancelled')]},
        }
        if not filterby:
            filterby = 'created'
        domain += searchbar_filters[filterby]['domain']
        service_job_count = freight_shipment.search_count(domain)

        pager = portal_pager(
            url="/dashboard/service_jobs_shipment",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=service_job_count,
            page=page,
            step=self._items_per_page
        )
        shipment_details = freight_shipment.search(domain, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'service_jobs': shipment_details.sudo(),
            'page_name': 'service_jobs_shipment',
            'pager': pager,
            'default_url': '/dashboard/service_jobs_shipment',
            'searchbar_filters': OrderedDict(searchbar_filters.items()),
            'filterby': filterby,
        })
        return request.render("ics_customer_portal_shipment_jobs.portal_my_service_jobs_shipment", values)

    @http.route(['/dashboard/service_jobs_shipment/<int:service_job_id>'], type='http', auth="public", website=True)
    def portal_service_jobs_shipment_page(self, service_job_id, report_type=None, access_token=None, message=False, download=False, error=False, **kw):
        try:
            service_shipment_sudo = self._document_check_access('freight.service.job', service_job_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if service_shipment_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('freight_house_shipment_view_%s' % service_shipment_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['freight_house_shipment_view_%s' % service_shipment_sudo.id] = now
                body = _('Shipment Jobs viewed by customer %s', service_shipment_sudo.client_id.name)
                _message_post_helper(
                    "freight.service.job",
                    service_shipment_sudo.id,
                    body,
                    token=service_shipment_sudo.access_token,
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=service_shipment_sudo.user_id.sudo().partner_id.ids,
                )
        values = {
            'service_job': service_shipment_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': service_shipment_sudo.client_id.id,
            'report_type': 'html',
            'error': error,
            'action': service_shipment_sudo._get_portal_return_action(),
            'document_type_ids': service_shipment_sudo.document_ids.mapped('document_type_id').filtered(lambda x: x.document_mode == 'in' and x.model_id.model == 'freight.service.job'),
        }
        if service_shipment_sudo.company_id:
            values['res_company'] = service_shipment_sudo.company_id
        return request.render('ics_customer_portal_shipment_jobs.service_jobs_shipment_portal_template', values)

    @http.route('/upload/service_job/document', type='http', auth='public', website=True)
    def upload_service_jobs_document(self, **kw):
        if kw.get('shipment_id'):
            house_shipment_id = request.env['freight.service.job'].browse(int(kw.get('shipment_id')))
            vals = {
                'name': kw.get('name'),
                'document_type_id': int(kw.get('document_id')),
                'document_mode': 'in',
                'is_publish': True,
            }
            query_string = ''
            if os.path.splitext(kw.get('file_name').filename)[1].lower() in ['.docx', '.doc', '.txt', '.odt', '.xlsx', '.xls', '.jpeg', '.png', '.pdf']:
                if kw.get('selected_document_id'):
                    if kw.get('file_name'):
                        vals.update({
                            'document_file_name': kw.get('file_name').filename,
                            'document_file': base64.b64encode(kw.get('file_name').read())
                        })
                    document = house_shipment_id.sudo().document_ids.filtered(lambda x: str(x.id) == kw.get('selected_document_id'))
                    document.sudo().write(vals)
                else:
                    vals.update({
                        'document_file_name': kw.get('file_name').filename,
                        'document_file': base64.b64encode(kw.get('file_name').read())
                    })
                    house_shipment_id.sudo().document_ids = [(0, 0, vals)]
            else:
                query_string = '&error=True'
            redirect_url = request.env.company.get_base_url() + house_shipment_id.sudo().get_service_portal_url() + query_string
            return request.redirect(redirect_url)
