# -*- coding: utf-8 -*-

import base64
import os
from collections import OrderedDict
from odoo import http, _, fields
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import pager as portal_pager


class FFJobsShipmentPortal(portal.CustomerPortal):

    _items_per_page = 10

    def _prepare_home_portal_values(self, counters):
        """
        Add FF jobs shipment counts
        """
        values = super()._prepare_home_portal_values(counters)
        freight_shipment = request.env['freight.house.shipment']
        if 'ff_jobs_shipment_count' in counters:
            values['ff_jobs_shipment_count'] = freight_shipment.search_count(self._prepare_ff_jobs_shipment_domain()) \
                if freight_shipment.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_ff_jobs_shipment_domain(self):
        return [
            ('state', 'in', ['booked', 'in_transit', 'arrived', 'completed']),
            ('client_id', '=', request.env.user.partner_id.id)
        ]

    @http.route(['/dashboard/ff_jobs_shipment', '/dashboard/ff_jobs_shipment/page/<int:page>'], type='http', auth="user", website=True)
    def portal_ff_jobs_shipment(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        freight_shipment = request.env['freight.house.shipment']
        domain = self._prepare_ff_jobs_shipment_domain()

        searchbar_filters = {
            'booked': {'label': _('Booked'), 'domain': [("state", "=", 'booked')]},
            'in_transit': {'label': _('In-Transit'), 'domain': [("state", "=", 'in_transit')]},
            'arrived': {'label': _('Arrived'), 'domain': [("state", "=", 'arrived')]},
            'completed': {'label': _('Completed'), 'domain': [("state", "=", 'completed')]},
        }
        if not filterby:
            filterby = 'booked'
        domain += searchbar_filters[filterby]['domain']
        ff_job_count = freight_shipment.search_count(domain)

        pager = portal_pager(
            url="/dashboard/ff_jobs_shipment",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=ff_job_count,
            page=page,
            step=self._items_per_page
        )

        shipment_details = freight_shipment.search(domain, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'ff_jobs': shipment_details.sudo(),
            'page_name': 'ff_jobs_shipment',
            'pager': pager,
            'default_url': '/dashboard/ff_jobs_shipment',
            'searchbar_filters': OrderedDict(searchbar_filters.items()),
            'filterby': filterby,
        })
        return request.render("ics_customer_portal_shipment.portal_my_ff_jobs_shipment", values)

    @http.route(['/dashboard/ff_jobs_shipment/<int:ff_jobs_id>'], type='http', auth="public", website=True)
    def portal_ff_job_shipment_page(self, ff_jobs_id, report_type=None, access_token=None, message=False, download=False, error=False, **kw):
        try:
            ff_jobs_sudo = self._document_check_access('freight.house.shipment', ff_jobs_id,
                                                       access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if ff_jobs_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('freight_house_shipment_view_%s' % ff_jobs_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['freight_house_shipment_view_%s' % ff_jobs_sudo.id] = now
                body = _('FF Jobs viewed by customer %s', ff_jobs_sudo.client_id.name)
                _message_post_helper(
                    "freight.house.shipment",
                    ff_jobs_sudo.id,
                    body,
                    token=ff_jobs_sudo.access_token,
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=ff_jobs_sudo.user_id.sudo().partner_id.ids,
                )
        shipment_id = request.env['freight.house.shipment'].sudo().browse(ff_jobs_id)

        container_ids = shipment_id.container_ids or shipment_id.package_ids
        cargo_details = {
            'POL': shipment_id.destination_port_un_location_id.name or shipment_id.road_destination_un_location_id.name,
            'POD': shipment_id.origin_port_un_location_id.name or shipment_id.road_origin_un_location_id.name,
            'Shipper Name': shipment_id.shipper_id.name,
            'Consignee Name': shipment_id.consignee_id.name,
            'Commodity': ", ".join(container.commodity_id.name for container in shipment_id.package_ids.mapped('commodity_ids')),
            'Number of Pieces': shipment_id.pack_unit,
            'Gross Weight': '{} {}'.format(shipment_id.gross_weight_unit, shipment_id.gross_weight_unit_uom_id.name),
            'Volume': '{} {}'.format(shipment_id.volume_unit, shipment_id.volume_unit_uom_id.name),
            'Container No': ','.join(container_ids.mapped('container_number.container_number')),
            'Customer Ref': shipment_id.client_id.ref,
            'Invoice No': ", ".join(move.name for move in shipment_id.move_ids.filtered(lambda move: move.move_type == 'out_invoice')),
        }
        values = {
            'ff_job': shipment_id,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': shipment_id.client_id.id,
            'report_type': 'html',
            'error': error,
            'action': shipment_id._get_portal_return_action(),
            'cargo_details': cargo_details,
            'document_type_ids': shipment_id.document_ids.mapped('document_type_id').filtered(lambda x: x.document_mode == 'in' and x.model_id.model == 'freight.house.shipment'),
        }
        if shipment_id.company_id:
            values['res_company'] = shipment_id.company_id
        return request.render('ics_customer_portal_shipment.ff_jobs_shipment_portal_template', values)

    @http.route('/upload/ff_jobs/document', type='http', auth='public', website=True)
    def upload_ff_jobs_document(self, **kw):
        if kw.get('shipment_id'):
            house_shipment_id = request.env['freight.house.shipment'].browse(int(kw.get('shipment_id')))
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
            redirect_url = request.env.company.get_base_url() + house_shipment_id.sudo().get_ff_portal_url() + query_string
            return request.redirect(redirect_url)
