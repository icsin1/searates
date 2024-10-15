from odoo import models, api
from odoo.addons.odoo_base import tools

class FreightShipmentDashboard(models.Model):
    _inherit = 'freight.master.shipment'

    @api.model
    def get_bookings_by_user_data(self, domain=[], limit=10, offset=0, **kwargs):
        return tools.prepare_group(self, domain=domain, fields=['create_uid'], limit=limit, offset=offset, format_dict={
            'Username': lambda x: self.env['res.users'].browse(x.get("create_uid")[0]).email,
            'Count': '__count'
        }, **kwargs)
