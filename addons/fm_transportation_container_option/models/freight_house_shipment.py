from odoo.exceptions import ValidationError
from odoo import models, _


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    def action_fetch_from_quote(self):
        self.ensure_one()
        if self.mode_type == 'land':
            quote = self.shipment_quote_id
            if self.cargo_is_package_group and self.package_ids:
                raise ValidationError(_('Remove existing packages to Fetch package data from Quote.'))
            if not self.cargo_is_package_group and self.container_ids:
                raise ValidationError(_('Remove existing container to Fetch container data from Quote.'))
            if self.cargo_is_package_group:
                # Package - LCL
                self.package_ids = [(0, 0, vals) for vals in quote._prepare_package_detail_vals()]
            else:
                # Container - FCL
                self.container_ids = [(0, 0, vals) for vals in quote._prepare_container_detail_vals()]
            self.with_context(force_change=True)._compute_auto_weight_volume()
        else:
            return super().action_fetch_from_quote()
