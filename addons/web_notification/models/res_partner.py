from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    web_last_notif_ack = fields.Datetime('Last notification marked as read', default=fields.Datetime.now)
