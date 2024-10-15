from odoo import models, fields


class FreightServiceJobMixin(models.AbstractModel):
    _name = 'freight.service.job.mixin'
    _description = 'Freight Service Job Mixin'
    _inherit = [
        'mail.thread', 'mail.activity.mixin',
        'freight.base.company.user.mixin', 'freight.departure.arrival.mixin', 'freight.origin.destination.location.mixin', 'freight.product.mixin', 'freight.cargo.weight.volume.mixin',
    ]
    _order = 'create_date DESC'

    sales_agent_id = fields.Many2one(
        'res.users', domain="[('company_id', '=', company_id)]", string="Sales Agent", required=True, default=lambda self: self.env.user, tracking=True)

    # Service Job details
    date = fields.Date(required=True)

    # Locations
    origin_port_name = fields.Char(related='origin_port_un_location_id.name', store=True, string='Origin Port Name')
    destination_port_name = fields.Char(related='destination_port_un_location_id.name', store=True, string='Destination Port Name')
