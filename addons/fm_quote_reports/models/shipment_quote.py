from odoo import models, fields, api


class ShipmentQuote(models.Model):
    _inherit = 'shipment.quote'

    status_history_ids = fields.One2many('shipment.quote.status.history', 'quote_id', string='Status History')

    def _track_template(self, changes):
        res = super()._track_template(changes)
        if 'state' in changes:
            for quote in self:
                quote.status_history_ids.sudo().create({
                    'quote_id': quote.id,
                    'user_id': self.env.user.id,
                    'status': quote.state,
                    'status_change_date': fields.Datetime.now()
                })
        return res
