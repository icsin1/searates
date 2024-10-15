# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HouseShipmentChargeRevenue(models.Model):
    _inherit = 'house.shipment.charge.revenue'

    status = fields.Selection(selection_add=[("pro_forma", "Pro Forma Invoice"),
                                             ("pro_forma_cancel", "Pro Forma Invoice Cancelled")],
                              ondelete={'pro_forma': 'set null', 'pro_forma_cancel': 'set null'})
    pro_forma_invoice_line_ids = fields.One2many('pro.forma.invoice.line', 'house_shipment_charge_revenue_id', string='Pro Forma Invoices')

    def _modification_line_restrict_states(self):
        states = super()._modification_line_restrict_states()
        states += ['pro_forma']
        return states

    @api.depends('amount_currency_residual', 'total_currency_amount',
                 'pro_forma_invoice_line_ids', 'pro_forma_invoice_line_ids.pro_forma_invoice_id.state')
    def _compute_invoice_status(self):
        super()._compute_invoice_status()
        for rec in self:
            if rec.pro_forma_invoice_line_ids and not rec.move_line_ids:
                if all(pro_forma_line.pro_forma_invoice_id.state == 'cancel' for pro_forma_line in rec.pro_forma_invoice_line_ids):
                    rec.status = 'pro_forma_cancel'
                if any(pro_forma_line.pro_forma_invoice_id.state != 'cancel' for pro_forma_line in rec.pro_forma_invoice_line_ids):
                    rec.status = 'pro_forma'

    def action_create_pro_forma_invoice(self):
        to_pro_forma_invoice = self.filtered(lambda l: l.status in ['no', 'pro_forma_cancel'])
        if not to_pro_forma_invoice:
            raise UserError(_("Nothing to pro-forma invoice."))
        if to_pro_forma_invoice[0].house_shipment_id.state == 'cancelled':
            raise UserError(_("Can not generate pro-forma invoice of cancelled shipment."))

        self.check_charges_rate_per_unit('pro-forma invoice')
        action = self.env.ref('fm_proforma.shipment_charge_pro_forma_invoice_wizard_action').sudo().read([])[0]
        cash_rounding_id = False
        if self.env.user.has_group('account.group_cash_rounding'):
            cash_rounding_id = self.env['account.cash.rounding'].search([], limit=1).id
        action['context'] = {
            'default_charge_ids': [(6, False, to_pro_forma_invoice.ids)],
            'default_currency_id': self.company_id.currency_id.id,
            'default_house_shipment_id': to_pro_forma_invoice[0].house_shipment_id.id,
            'default_invoice_cash_rounding_id': cash_rounding_id
        }
        return action

    def _prepare_pro_forma_invoice(self):
        self.ensure_one()
        pro_forma_invoice_vals = {
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'company_id': self.house_shipment_id.company_id.id,
            'house_shipment_id': self.house_shipment_id.id,
            'pro_forma_invoice_line_ids': [
                (0, 0, self._prepare_pro_forma_invoice_line())
            ],
        }
        return pro_forma_invoice_vals

    def _prepare_pro_forma_invoice_line(self):
        pro_forma_invoice_line_vals = {
            'service_name': self.charge_description,
            'product_id': self.product_id.id,
            'product_uom_id': self.uom_id.id,
            'quantity': self.quantity,
            'sell_currency_id': self.currency_id.id,
            'price_unit': self.amount_rate,
            'tax_ids': [(6, 0, self.tax_ids.ids)],
            'house_shipment_charge_revenue_id': self.id
            }
        return pro_forma_invoice_line_vals

    def action_view_pro_forma_invoice(self):
        pro_forma_invoice_ids = self.pro_forma_invoice_line_ids.mapped('pro_forma_invoice_id')
        return self.view_pro_forma_invoice(pro_forma_invoice_ids)

    def view_pro_forma_invoice(self, pro_forma_invoice_ids):
        tree_view_id = self.env.ref('fm_proforma.pro_forma_invoice_view_tree').id
        form_view_id = self.env.ref('fm_proforma.pro_forma_invoice_view_form').id
        action = {
            'name': _('Pro Forma Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'pro.forma.invoice',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
        }
        if len(pro_forma_invoice_ids) > 1:
            house_shipment_ids = pro_forma_invoice_ids.mapped('house_shipment_id')
            action['domain'] = [('house_shipment_id', 'in', house_shipment_ids.ids)]
        elif len(pro_forma_invoice_ids) == 1:
            form_view = [(self.env.ref('fm_proforma.pro_forma_invoice_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pro_forma_invoice_ids.id
        return action
