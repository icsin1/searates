from odoo import models, fields
from odoo.addons.fm_quote.models.shipment_quote import STATES


class ShipmentQuoteStatusHistory(models.Model):
    _name = 'shipment.quote.status.history'
    _description = 'Quote Status Analysis'
    _rec_name = 'quote_id'
    _order = 'status_change_date DESC'

    quote_id = fields.Many2one('shipment.quote', required=True, string='Quote', ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True, string='Status Changed By')
    company_id = fields.Many2one('res.company', related='quote_id.company_id', store=True)
    status = fields.Selection(STATES, required=True)
    status_change_date = fields.Datetime(readonly=True, string='Changed On')
