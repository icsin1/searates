# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _invoice_billed(self):
        self.total_billed = 0
        if not self.ids:
            return True

        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self.filtered('id'):
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        domain = [
            ('partner_id', 'in', all_partner_ids),
            ('state', 'not in', ['draft', 'cancel']),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
        ]
        price_totals = self.env['account.invoice.report'].read_group(domain, ['price_subtotal'], ['partner_id'])
        for partner, child_ids in all_partners_and_children.items():
            partner.total_billed = sum(price['price_subtotal'] for price in price_totals if price['partner_id'][0] in child_ids)

    total_billed = fields.Monetary(compute='_invoice_billed', string="Total Billed", groups='account.group_account_invoice,account.group_account_readonly')

    def action_view_partner_bills(self):
        self.ensure_one()
        all_child = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        domain = [
            ('move_type', 'in', ('in_invoice', 'in_refund')),
            ('partner_id', 'in', all_child.ids)
        ]
        context = {
            'default_move_type': 'in_invoice',
            'default_partner_id': self.id,
            'move_type': 'in_invoice',
            'active_test': False,
            'tree_view_ref': 'account.view_in_invoice_bill_tree'
        }
        return {
            'name': _('Bills'),
            'type': 'ir.actions.act_window',
            'domain': domain,
            'context': context,
            'view_type': 'list',
            'view_mode': 'list,form',
            'res_model': 'account.move',
        }

    @api.model
    def create(self, vals):
        vals = self._update_category_ids(vals)
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        if 'res_partner_search_mode' in self._context:
            vals = self._update_category_ids(vals)
        return super(ResPartner, self).write(vals)

    def _update_category_ids(self, vals):
        default_supplier_rank = self._context.get('default_supplier_rank', 0)
        res_partner_search_mode = self._context.get('res_partner_search_mode')

        if default_supplier_rank == 1 and res_partner_search_mode == 'supplier':
            org_type_vendor_id = self.env.ref('freight_base.org_type_vendor', raise_if_not_found=False).id
            vals.update({'category_ids': [(4, org_type_vendor_id)]})

        elif default_supplier_rank != 1 and res_partner_search_mode == 'customer':
            org_type_customer_id = self.env.ref('freight_base.org_type_customer', raise_if_not_found=False).id
            vals.update({'category_ids': [(4, org_type_customer_id)]})

        return vals
