from odoo import api, fields, models


class ActionLogs(models.Model):
    _name = 'ir.audit.log.action'
    _description = 'Audit Action Logs'
    _order = "create_date desc"

    action_id = fields.Many2one('ir.actions.actions', 'Action')
    action_dump = fields.Text('Action Dump(JSON)')
    menu_id = fields.Many2one('ir.ui.menu', 'Menu')
    user_id = fields.Many2one('res.users', 'User')
    action_type = fields.Char('Action Type', related='action_id.type')
    operation_date_time = fields.Datetime('Operation Date Time', default=lambda self: fields.datetime.now())
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)

    @api.autovacuum
    def _delete_action_logs(self):
        ics_ir_log_history = self.env['ir.config_parameter'].sudo().get_param('ics_ir_audit_log.ics_ir_log_history', 180)
        self._cr.execute("DELETE FROM ir_audit_log_action WHERE create_date < NOW() - INTERVAL '%d days'" % int(ics_ir_log_history))
