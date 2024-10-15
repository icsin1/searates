from odoo import models, fields


class MasterShipmentExpenseEntryWizard(models.TransientModel):
    _name = 'master.shipment.expense.entry.wizard'
    _inherit = 'master.shipment.charge.bill.wizard'
    _description = 'Generating Expense Entry'

    company_id = fields.Many2one('res.company')
    charge_ids = fields.Many2many(
        'master.shipment.charge.cost', 'master_cost_wizard_expense_rel', 'wizard_id', 'charge_id', string='Charges',
        domain="[('master_shipment_id', '=', master_shipment_id), ('status', '=', 'no')]")

    line_ids = fields.One2many('master.shipment.expense.entry.wizard.line', 'wizard_id', string='Entry Lines')
    journal_id = fields.Many2one('account.journal', domain="[('type', '=', 'general'),('company_id','=', company_id)]", required=True)
    payment_account_id = fields.Many2one('account.account', domain="[('user_type_id.internal_group', '=', 'asset'), ('company_id','=', company_id)]", required=True)
    single_currency_billing = fields.Boolean(default=True)

    def action_generate_bills(self):
        move_type = 'entry'
        invoices = []
        for line in self.line_ids:
            invoices.append(line._generate_invoice(move_type))
        AccountMove = self.env['account.move'].with_context(default_move_type=move_type)
        moves = AccountMove.create(invoices)
        # Force on change partner
        for move in moves:
            move.with_context(skip_reset_line=True)._onchange_partner_id()
        return self.action_view_invoice(moves, move_type)

    def action_view_invoice(self, invoices, move_type):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        action['context'] = {'create': 0}
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
            return action

        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        action['views'] = form_view + [(state, view) for state, view in action.get('views', []) if view != 'form']
        action['res_id'] = invoices.id
        return action


class ShipmentExpenseEntryWizardLine(models.TransientModel):
    _name = 'master.shipment.expense.entry.wizard.line'
    _inherit = 'shipment.charge.bill.wizard.line'
    _description = 'Invoice Lines'

    wizard_id = fields.Many2one('master.shipment.expense.entry.wizard', required=True, ondelete='cascade')
    charge_ids = fields.Many2many('master.shipment.charge.cost', 'master_exp_entry_line_wizard_charge_rel', 'wizard_id', 'charge_id', string='Charges')

    def _generate_invoice(self, move_type):
        self.ensure_one()
        master_shipment = self.wizard_id.master_shipment_id
        return {
            'move_type': move_type,
            'currency_id': self.currency_id.id,
            'user_id': self.env.user.id,
            'ref': ','.join(self.wizard_id.master_shipment_id.mapped('name')),
            'invoice_user_id': self.env.user.id,
            'journal_id': self.wizard_id.journal_id.id,
            'invoice_origin': master_shipment.display_name,
            'company_id': master_shipment.company_id.id,
            'line_ids': self._prepare_invoice_line(),
            'invoice_date': fields.Date.context_today(self),
            'from_shipment_charge': True,
            'add_charges_from': 'master',
            'charge_master_shipment_ids': [(6, 0, self.wizard_id.master_shipment_id.ids)]
        }

    def _prepare_invoice_line(self):
        self.ensure_one()
        charge_lines = []
        total_charges = 0
        for charge in self.charge_ids:
            currency_exchange_rate = self.wizard_id.get_exchange_rate(charge)
            charge_rate = charge.amount_currency_id.with_context(currency_exchange_rate=currency_exchange_rate)._convert(
                charge.amount_rate,
                self.currency_id,
                charge.master_shipment_id.company_id,
                charge.master_shipment_id.shipment_date,
                round=False
            ) or 1

            total_charge_amount = charge_rate * charge.quantity

            charge_lines.append((0, 0, {
                'account_id': charge.property_account_id.id,
                'name': '{}'.format(charge.charge_description),
                'product_id': charge.product_id.id,
                'product_uom_id': charge.product_id.uom_id.id,
                'amount_currency': charge.amount_rate,
                'currency_id': charge.amount_currency_id.id,
                'debit': total_charge_amount,
                'tax_ids': [(6, 0, [])],
                'master_shipment_charge_cost_id': charge.id,
                'shipment_charge_currency_id': charge.amount_currency_id.id
            }))
            total_charges += total_charge_amount

        # Balance to payment account
        charge_lines.append((0, 0, {
            'account_id': self.wizard_id.payment_account_id.id,
            'amount_currency': total_charges,
            'credit': total_charges,
        }))
        return charge_lines
