# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    views = env['ir.ui.view'].search([('model', 'in', ('account.move', 'account.payment')), ('is_custom', '=', True)])
    views.unlink()
    invoice_filter = env.ref('ics_account.view_account_invoice_filter', raise_if_not_found=False)
    if invoice_filter:
        invoice_filter.unlink()
    tree_ics_account = env.ref('ics_account.view_invoice_tree_inherit_ics_account', raise_if_not_found=False)
    if tree_ics_account:
        tree_ics_account.unlink()
    payment_search = env.ref('ics_account.view_account_payment_search', raise_if_not_found=False)
    if payment_search:
        payment_search.unlink()
    payment_tree = env.ref('ics_account.view_account_payment_tree_inherit_ics_account', raise_if_not_found=False)
    if payment_tree:
        payment_tree.unlink()

    # Keep existing system generated number to backend field
    cr.execute("""ALTER TABLE account_move ADD COLUMN IF NOT EXISTS old_name varchar""")
    cr.execute("""UPDATE account_move SET old_name=name WHERE old_name != null""")

    for company in env['res.company'].sudo().search([]):
        cr.execute("""
            UPDATE account_move AS t
            SET
                reference_number = t.reference_number || ' (* ' || t.id || ')'
            FROM (
                SELECT reference_number, MIN(id) as min_id
                FROM account_move
                GROUP BY reference_number
                HAVING COUNT(*) > 1
            ) AS dup
            WHERE
                t.reference_number = dup.reference_number and t.company_id = {} and t.reference_number != '/'
            AND
                t.id <> dup.min_id;
        """.format(company.id))
        cr.execute("""
            UPDATE account_payment AS ap
            SET
                reference_number = ap.reference_number || ' (* ' || ap.id || ')'
            FROM (
                SELECT ap.reference_number, MIN(am.id) as min_id
                FROM account_move AS am
                JOIN account_payment AS ap ON am.id = ap.move_id
                WHERE am.company_id = {}
                GROUP BY ap.reference_number
                HAVING COUNT(*) > 1
            ) AS dup
            WHERE
                ap.reference_number = dup.reference_number
            AND
                ap.id <> dup.min_id;
        """.format(company.id))
        cr.commit()

    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("select id, reference_number from account_move where name != reference_number and reference_number not in ('/', '')")
    data = dict(cr.fetchall())
    for move in env['account.move'].sudo().search([('state', '!=', 'draft')]):
        if move.id in data:
            move.write({'name': data.get(move.id)})
    cr.commit()
