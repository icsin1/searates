from odoo import models, fields, _

Account_journal_tracking_fields = [
    'type_control_ids',
    'account_control_ids'
    ]


class AccountJournal(models.Model):

    _inherit = "account.journal"

    name = fields.Char(tracking=True)
    code = fields.Char(tracking=True)
    type = fields.Selection(tracking=True)
    default_account_type = fields.Many2one(tracking=True)
    default_account_id = fields.Many2one(tracking=True)
    suspense_account_id = fields.Many2one(tracking=True)
    profit_account_id = fields.Many2one(tracking=True)
    loss_account_id = fields.Many2one(tracking=True)
    bank_statements_source = fields.Selection()
    bank_acc_number = fields.Char(tracking=True)
    bank_id = fields.Many2one(tracking=True)
    bank_account_id = fields.Many2one(tracking=True)
    sale_activity_type_id = fields.Many2one(tracking=True)
    sale_activity_user_id = fields.Many2one(tracking=True)
    sale_activity_note = fields.Text(tracking=True)
    invoice_reference_type = fields.Selection(tracking=True)
    invoice_reference_model = fields.Selection(tracking=True)
    currency_id = fields.Many2one(tracking=True)
    company_id = fields.Many2one(tracking=True)
    country_code = fields.Char(tracking=True)
    refund_sequence = fields.Boolean(tracking=True)
    restrict_mode_hash_table = fields.Boolean(tracking=True)

    def _prepare_account_journal_tracking_msg(self, tracking_fields):
        self.ensure_one()
        track_fields = tracking_fields[self.id]
        msg = "<p>For Many2many</p>"
        msg += "<ul>"
        for field_name, value in track_fields.items():
            field_info = self.fields_get([field_name])[field_name]
            old_value = value
            new_value = self[field_name]
            if field_info.get('type') == "many2many":
                old_value = old_value
                new_value = new_value
            msg += """
                <li>
                    {}: {}
                    <span class="fa fa-long-arrow-right" style='vertical-align: middle;'/>
                    {}
                </li>""".format(field_info.get('string'), old_value, new_value)
        msg += "</ul>"
        return msg

    def _get_account_journal_tracking(self, vals={}):
        self.ensure_one()
        tracking_fields_values = {}
        updated_fields = set(vals.keys()).intersection(set(Account_journal_tracking_fields))
        value_changed = False
        for updated_field in updated_fields:
            field_info = self.fields_get([updated_field])[updated_field]
            if field_info.get('type') == "many2many":
                current_records = self[updated_field].ids
                updated_records = vals.get(updated_field, [(6, 0, [])])[0][2]

                if set(current_records) != set(updated_records):
                    value_changed = True
            else:
                if vals.get(updated_field) != self[updated_field]:
                    value_changed = True

        if updated_fields and value_changed:
            for key in Account_journal_tracking_fields:
                tracking_fields_values.update({
                    key: self[key]
                })
        return tracking_fields_values

    def write(self, vals):
        tracking_fields = {}
        for account in self:
            tracking_fields[account.id] = account._get_account_journal_tracking(vals)
        res = super().write(vals)
        for account in self:
            # Logging declared weight volume fields change log
            if tracking_fields.get(account.id):
                msg = account._prepare_account_journal_tracking_msg(tracking_fields)
                account._message_log(body=msg,)
        return res

    def action_open_reconcile(self):
        # Open reconciliation view for bank statements belonging to this journal
        bank_stmt = (
            self.env["account.bank.statement"]
            .search([("journal_id", "in", self.ids)])
            .mapped("line_ids")
        )
        return {
            "type": "ir.actions.client",
            "tag": "bank_statement_reconciliation_view",
            "context": {
                "statement_line_ids": bank_stmt.ids,
                "company_ids": self.mapped("company_id").ids,
            },
        }

    def action_open_reconcile_to_check(self):
        self.ensure_one()
        ids = self.to_check_ids().ids
        action_context = {
            "show_mode_selector": False,
            "company_ids": self.mapped("company_id").ids,
            "suspense_moves_mode": True,
            "statement_line_ids": ids,
        }
        return {
            "type": "ir.actions.client",
            "tag": "bank_statement_reconciliation_view",
            "context": action_context,
        }


class AccountPaymentMethodLine(models.Model):
    _inherit = "account.payment.method.line"

    def write(self, vals):
        fields = self._fields.keys()
        vals_keys = vals.keys()
        msg = ''
        for key in vals_keys:
            if key in fields:
                old_value = self[key]
                new_value = vals[key]
                if self._fields[key].type == 'binary':
                    old_value = "none"
                    new_value = "none"
                if self._fields[key].type == 'many2many':
                    old_value = 'none'
                    new_value = 'none'
                if self._fields[key].type == 'many2one':
                    old_value = self[key].name or self[key].id
                    model = self._fields[key].comodel_name
                    new_value = self.env[model].browse(vals[key]).name or self.env[model].browse(vals[key]).id
                msg += _(
                    "%(field_name)s : %(old_qty)s -> %(new_qty)s",
                    old_qty=old_value,
                    new_qty=new_value,
                    field_name=self._fields[key].string
                ) + "<br/>"
        self.journal_id and self.journal_id.sudo().message_post(body=msg or '')
        res = super().write(vals)
        return res
