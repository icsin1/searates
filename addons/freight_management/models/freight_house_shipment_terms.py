from odoo import models, fields, api


class FreightHouseShipmentTerms(models.Model):
    _name = 'freight.house.shipment.terms'
    _inherit = 'freight.shipment.terms.mixin'
    _description = 'House Shipment Terms'
    _rec_name = 'shipment_id'

    @api.model
    def _get_document_type_domain(self):
        return super()._get_document_type_domain() + [('model_id.model', '=', 'freight.house.shipment')]

    shipment_id = fields.Many2one('freight.house.shipment', ondelete='cascade', required=True)
    document_type_id = fields.Many2one('freight.document.type', required=True, domain=_get_document_type_domain)

    _sql_constraints = [
        ('document_type_and_shipment_unique', 'UNIQUE(document_type_id,shipment_id)', "Document Type already exists.")
    ]
