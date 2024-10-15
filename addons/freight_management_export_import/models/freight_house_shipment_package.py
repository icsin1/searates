from odoo import models


class FreightHouseShipmentPackage(models.Model):
    _inherit = 'freight.house.shipment.package'

    def copy_data(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if self.shipment_id and self.shipment_id.import_company_id:
            default['package_group_ids'] = [(0, 0, package_group.copy_data()[0]) for package_group in self.package_group_ids]
        return super().copy_data(default=default)
