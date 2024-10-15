import logging
import traceback
from odoo import models, fields
from .cargoesflow_api import CargoesflowAPI

_logger = logging.getLogger(__name__)


class ShipmentPackageMixin(models.AbstractModel):
    _inherit = 'freight.shipment.package.mixin'

    tracking_url = fields.Char('Tracking URL')

    def _get_tracking_url(self):
        self.ensure_one()
        tracking_url = self.tracking_url
        try:
            if self.container_number and not self.tracking_url:
                cargoesflow_api = CargoesflowAPI(self.env)
                tracking_url = cargoesflow_api._get_container_tracking_url(self.container_number.name)
                self.write({'tracking_url': tracking_url})
        except Exception as e:
            _logger.warn(str(e))
            traceback.print_exc()
        return tracking_url

    def action_track_shipment_milestone_container(self):
        tracking_url = self._get_tracking_url()
        if tracking_url:
            return {
                'type': 'ir.actions.act_url',
                'url': tracking_url,
                'target': 'new',
            }
