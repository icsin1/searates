from odoo import models, fields, api


class FreightDocumentType(models.Model):
    _name = 'freight.document.type'
    _description = 'Freight Document Type'
    _order = 'sequence'

    name = fields.Char(string='Document Type', required=True)
    model_id = fields.Many2one('ir.model', ondelete='cascade', string='Related Model', required=True)
    document_mode = fields.Selection([
        ('in', 'IN'),
        ('out', 'OUT'),
    ], string="Document Mode", required=True)

    # FIXME: Deprecated field will be removed in future
    report_template_id = fields.Many2one('docx.template', string='Document Report', domain="[('res_model_id', '=', model_id)]", ondelete='set null')

    report_template_ref_id = fields.Reference(selection=[
        ('docx.template', 'DOCX')
    ], string='Document Template')

    report_action_id = fields.Many2one('ir.actions.report', compute='_compute_report_action_id', store=True)

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    def get_document_information(self):
        self.ensure_one()
        if self.report_template_ref_id:
            report_template = self.report_template_ref_id
            values = report_template.read(['id', 'name', 'show_wizard', 'output_type'])[0]
            values.update({
                'report_res_model': report_template._name,
                'report_res_id': report_template.id
            })
            return values
        return {}

    @api.depends('report_template_ref_id')
    def _compute_report_action_id(self):
        for rec in self:
            if rec.report_template_ref_id:
                rec.report_action_id = rec.report_template_ref_id.report_id.id
            else:
                rec.report_action_id = False
