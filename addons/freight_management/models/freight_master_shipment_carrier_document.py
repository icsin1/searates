from odoo import models, fields


class FreightMaterShipmentCarrierDocument(models.Model):
    _name = 'freight.master.shipment.carrier.document'
    _description = 'Shipment Carrier Document'

    name = fields.Char('Document Name')
    shipment_id = fields.Many2one('freight.master.shipment', required=True, ondelete='cascade')
    document_file = fields.Binary(string='Documents')
    file_name = fields.Char(string='File Name')
