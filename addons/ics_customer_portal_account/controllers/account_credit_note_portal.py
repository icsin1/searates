# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class AccountCreditNotePortal(portal.CustomerPortal):

    _items_per_page = 10

    def _prepare_home_portal_values(self, counters):
        values = super(AccountCreditNotePortal, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        account_credit_note_obj = request.env['account.move']
        if 'account_credit_note_count' in counters:
            values['account_credit_note_count'] = account_credit_note_obj.search_count(self._prepare_account_credit_note_domain(partner)) \
                if account_credit_note_obj.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_account_credit_note_domain(self, partner):
        return [
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_refund'),
            ('state', '=', 'posted')
        ]

    @http.route(['/dashboard/account_credit_note', '/dashboard/account_credit_note/page/<int:page>'], type='http', auth="user", website=True)
    def portal_account_credit_note(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        account_credit_note_obj = request.env['account.move']
        domain = self._prepare_account_credit_note_domain(partner)

        account_credit_count = account_credit_note_obj.search_count(domain)
        pager = portal_pager(
            url="/dashboard/account_credit_note",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=account_credit_count,
            page=page,
            step=self._items_per_page
        )
        account_credit_note_invoice_ids = account_credit_note_obj.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'account_credit_note_invoice_ids': account_credit_note_invoice_ids.sudo(),
            'page_name': 'account_credit_note',
            'pager': pager,
            'default_url': '/dashboard/account_credit_note'
        })
        return request.render("ics_customer_portal_account.portal_my_account_credit_note", values)
