from odoo import models, fields


class FreightDocumentType(models.Model):
    _inherit = 'freight.document.type'

    report_template_ref_id = fields.Reference(selection_add=[
        ('stimulsoft.mrt.report', 'MRT Report')
    ], string='Related Template', ondelete={'stimulsoft.mrt.report': 'set null'})
