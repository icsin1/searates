from odoo import models, fields, api, _


class FreightProduct(models.Model):
    _name = 'freight.product'
    _description = 'Freight Product'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    name = fields.Char(required=True, string='Freight Product')
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade', string='Model')
    model_name = fields.Char(related='model_id.model', store=True, string='Model Name')
    match_domain = fields.Text(string='Shipment Matching Rule')
    product_type = fields.Selection(selection=[('general', 'General')], required=True, default='general')
    description = fields.Text()

    _sql_constraints = [
        ('name_freight_product_unique', 'unique(name,model_id,product_type)', 'The Freight Product with same name and product type for model already exists !')
    ]

    @api.depends('name', 'model_id.name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "{} ({})".format(rec.name, rec.model_id.name)

    def copy(self, default=None):
        self.ensure_one()
        chosen_name = default.get('name') if default else ''
        new_name = chosen_name or _('%s (copy)', self.name)
        default = dict(default or {}, name=new_name)
        return super(FreightProduct, self).copy(default)
