from odoo import models, fields


class FreightHouseShipmentCustomsDocument(models.Model):
    _name = 'freight.house.shipment.customs.document'
    _description = 'Shipment Customs Document'

    name = fields.Char('Document Name')
    shipment_id = fields.Many2one('freight.house.shipment', required=True, ondelete='cascade')

    # Custom Attributes
    declaration_date = fields.Date('Declaration Date')
    declaration_number = fields.Char('Declaration No.')
    customs_clearance_datetime = fields.Datetime(string='Clearance Date & Time')
    note = fields.Char(string='Note')
    document_file = fields.Binary(string='Documents')
    file_name = fields.Char(string='File Name')
