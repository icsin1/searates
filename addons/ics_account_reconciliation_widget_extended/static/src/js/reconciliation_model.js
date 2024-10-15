odoo.define("ics_account_reconciliation_widget_extended.ReconciliationModel", function (require) {
    "use strict";

    var StatementModel = require('account.ReconciliationModel').StatementModel;
    var field_utils = require("web.field_utils");
    var session = require("web.session");

    StatementModel.include({
        addProposition: function (handle, mv_line_id) {
            var line = this.getLine(handle);
            var prop = _.clone(_.find(line["mv_lines_" + line.mode], {id: mv_line_id}));
            var balance = line.balance.amount;
            var prop_amount = prop.partial_amount || prop.amount;
            var format_options = {currency_id: line.st_line.currency_id};
            if (balance > 0.00 && this._amountCompare(prop_amount, balance, line.st_line.currency_id) > 0){
                prop.partial_amount = balance;
                prop.partial_amount_str = field_utils.format.monetary(prop.partial_amount, {}, format_options);
            } else if (balance < 0.00 && this._amountCompare(prop_amount, balance, line.st_line.currency_id) < 0) {
                prop.partial_amount = balance;
                prop.partial_amount_str = field_utils.format.monetary(-prop.partial_amount, {}, format_options);
            }
            this._addProposition(line, prop);
            line["mv_lines_" + line.mode] = _.filter(
                line["mv_lines_" + line.mode],
                (l) => l.id !== mv_line_id
            );

            // Remove all non valid lines
            line.reconciliation_proposition = _.filter(
                line.reconciliation_proposition,
                function (prop) {
                    return prop && !prop.invalid;
                }
            );

            // Onchange the partner if not already set on the statement line.
            if (
                !line.st_line.partner_id &&
                line.reconciliation_proposition &&
                line.reconciliation_proposition.length === 1 &&
                prop.partner_id &&
                line.type === undefined
            ) {
                return this.changePartner(
                    handle,
                    {id: prop.partner_id, display_name: prop.partner_name},
                    true
                );
            }

            return Promise.all([
                this._computeLine(line),
                this._performMoveLine(
                    handle,
                    "match_rp",
                    line.mode === "match_rp" ? 1 : 0
                ),
                this._performMoveLine(
                    handle,
                    "match_other",
                    line.mode === "match_other" ? 1 : 0
                ),
            ]);
        },
        _amountCompare: function(value1, value2, currency_id){
            const currency = session.get_currency(currency_id);
            const delta = parseFloat((value1 - value2).toFixed(currency.digits[1]));
            if(delta > 0){
                return 1;
            } else if(delta < 0){
                return -1;
            } else {
                return 0;
            }
        },
    });
});