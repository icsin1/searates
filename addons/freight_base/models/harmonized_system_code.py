from odoo import models, fields, api


class HarmonizedSystemCode(models.Model):
    _name = 'harmonized.system.code'
    _description = 'Harmonized System Code'
    _order = 'code'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    name = fields.Char(string='Name', required=True)
    description = fields.Text()
    code = fields.Char(string='Code')
    code_range = fields.Char(compute="_compute_code_range", store=True)
    parent_id = fields.Many2one('harmonized.system.code', string='Parent')
    child_ids = fields.One2many('harmonized.system.code', 'parent_id', string="Sub Codes")
    child_count = fields.Integer(compute='_compute_child_count', store=True)
    country_id = fields.Many2one('res.country', string="For Country")

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "[%s] %s" % (rec.code, rec.name) if rec.code else rec.name

    @api.depends('child_ids', 'child_ids.code')
    def _compute_code_range(self):
        for rec in self:
            rec.code_range = "%s-%s" % (rec.child_ids[0].code, rec.child_ids[-1].code) if rec.child_ids else ''

    @api.depends('child_ids')
    def _compute_child_count(self):
        for rec in self:
            rec.child_count = len(rec.child_ids)
