from odoo import models, fields


class ProductJsonSpecification(models.Model):
    _inherit = 'product.json.specification'

    json_type = fields.Selection(selection_add=[('document', 'Document')], ondelete={'document': 'set default'})
    mrt_document_ids = fields.One2many('stimulsoft.mrt.report', 'json_spec_id', string='Related MRT Documents')
    mrt_product_document_ids = fields.One2many('stimulsoft.mrt.report.product', 'json_spec_id', 'Related MRT Product Documents')
