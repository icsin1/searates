from odoo import api, fields, models


class LoginLogs(models.Model):
    _name = 'ir.audit.log.auth'
    _description = 'Audit Login Logs'
    _order = "create_date desc"

    @api.autovacuum
    def _delete_login_logs(self):
        ics_ir_log_history = self.env['ir.config_parameter'].sudo().get_param('ics_ir_audit_log.ics_ir_log_history', 180)
        self._cr.execute("DELETE FROM ir_audit_log_auth WHERE create_date < NOW() - INTERVAL '%d days'" % int(ics_ir_log_history))

    user_id = fields.Many2one('res.users', 'User')
    login_date_time = fields.Datetime('Login Date Time', default=lambda self: fields.datetime.now())
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)


class LoginUserDetail(models.Model):
    _inherit = 'res.users'

    @api.model
    def _check_credentials(self, password, user_agent_env):
        result = super(LoginUserDetail, self)._check_credentials(password, user_agent_env)
        self.env['ir.audit.log.auth'].sudo().create({'user_id': self.id})
        return result
