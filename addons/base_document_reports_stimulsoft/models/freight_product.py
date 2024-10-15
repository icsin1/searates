from odoo import models, fields


class FreightProduct(models.Model):
    _inherit = 'freight.product'

    product_type = fields.Selection(selection_add=[('document', 'Document')], ondelete={'document': 'cascade'})
