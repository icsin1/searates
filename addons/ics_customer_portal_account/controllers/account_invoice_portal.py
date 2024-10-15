# -*- coding: utf-8 -*-

from collections import OrderedDict
from odoo import fields, http, _
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class AccountInvoicePortal(portal.CustomerPortal):

    _items_per_page = 10

    def _prepare_home_portal_values(self, counters):
        values = super(AccountInvoicePortal, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        account_invoice_obj = request.env['account.move']
        if 'account_invoice_count' in counters:
            values['account_invoice_count'] = account_invoice_obj.search_count(self._prepare_account_invoice_domain(partner)) \
                if account_invoice_obj.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_account_invoice_domain(self, partner):
        return [('partner_id', '=', partner.id), ('move_type', '=', 'out_invoice')]

    @http.route(['/dashboard/account_invoice', '/dashboard/account_invoice/page/<int:page>'], type='http', auth="user", website=True)
    def portal_account_invoice(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        account_invoice_obj = request.env['account.move']
        domain = self._prepare_account_invoice_domain(partner)

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'pending': {'label': _('Pending'), 'domain': self.get_due_invoices()},
            'overdue': {'label': _('Overdue'), 'domain': self.get_overdue_invoices()},
        }

        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        invoice_count = account_invoice_obj.search_count(domain)
        pager = portal_pager(
            url="/dashboard/account_invoice",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )
        account_invoice_ids = account_invoice_obj.search(domain, limit=self._items_per_page, offset=pager['offset'])
        overdue_move_domain = self.get_overdue_invoices(self._prepare_account_invoice_domain(partner))
        due_move_domain = self.get_due_invoices(self._prepare_account_invoice_domain(partner))
        overdue_move_ids = account_invoice_obj.search(overdue_move_domain)
        pending_move_ids = account_invoice_obj.search(due_move_domain)

        total_overdue_amt = f'{sum(overdue_move_ids.mapped("amount_residual_signed"))} {request.env.company.currency_id.name}'
        total_due_amt = f'{sum(pending_move_ids.mapped("amount_residual_signed"))} {request.env.company.currency_id.name}'

        values.update({
            'account_invoice_ids': account_invoice_ids.sudo(),
            'page_name': 'account_invoice',
            'pager': pager,
            'default_url': '/dashboard/account_invoice',
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'total_due_amt': total_due_amt,
            'total_overdue_amt': total_overdue_amt
        })
        return request.render("ics_customer_portal_account.portal_my_account_invoice", values)

    def get_overdue_invoices(self, domain=[]):
        overdue_domain = [('invoice_date_due', '<', fields.Date.today()), ('payment_state', 'not in', ['done', 'reversed'])]
        if domain:
            domain.extend(overdue_domain)
            return domain
        return overdue_domain

    def get_due_invoices(self, domain=[]):
        due_invoice_domain = [('invoice_date_due', '>=', fields.Date.today()), ('payment_state', 'not in', ['done', 'reversed'])]
        if domain:
            domain.extend(due_invoice_domain)
            return domain
        return due_invoice_domain
