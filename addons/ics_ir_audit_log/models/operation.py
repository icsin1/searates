from odoo import api, fields, models


class AuditLogOperation(models.Model):
    _name = 'ir.audit.log.operation'
    _description = 'Audit Log Operation'
    _order = "operation_date_time desc, operation_type, user_id"

    name = fields.Char("Resource Name")
    res_id = fields.Integer(string='ID')
    model_id = fields.Many2one('ir.model')
    res_model = fields.Char('Model', related='model_id.model')
    user_id = fields.Many2one('res.users', 'User')
    operation_type = fields.Selection([
        ('read', 'Read'),
        ('write', 'Write'),
        ('create', 'Create'),
        ('unlink', 'Delete')], string='Operation Type')
    operation_date_time = fields.Datetime('Operation Date Time', default=lambda self: fields.datetime.now())
    change_values = fields.Html('Change Logs')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)

    @api.autovacuum
    def _delete_operation_logs(self):
        ics_ir_log_history = self.env['ir.config_parameter'].sudo().get_param('ics_ir_audit_log.ics_ir_log_history', 180)
        self._cr.execute("DELETE FROM ir_audit_log_operation WHERE create_date < NOW() - INTERVAL '%d days'" % int(ics_ir_log_history))
