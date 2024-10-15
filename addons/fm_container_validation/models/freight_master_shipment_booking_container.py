from odoo import models, api, _
from odoo.exceptions import ValidationError
from stdnum.iso6346 import is_valid as is_valid_container_number


class FreightShipmentContainerNumber(models.Model):
    _inherit = 'freight.master.shipment.container.number'

    _sql_constraints = [
        ('container_number_unique', 'UNIQUE(container_number)', 'Container Number must be unique!')
    ]

    @api.onchange('container_number')
    @api.constrains('container_number')
    def _check_container_number(self):
        super()._check_container_number()
        for container_num in self:
            if container_num.container_number and not is_valid_container_number(container_num.container_number):
                raise ValidationError(_('Invalid Container Number:%s. Provide ISO 6346 Standard Container Number') % (container_num.container_number))

    def _validate_container_number(self, container_number_list):
        """
        Checks for given container number [type: list]
        returns invalid container number [type: list] if any
        """
        return [container_num for container_num in container_number_list if not is_valid_container_number(container_num)]

    @api.constrains('container_number', 'is_part_bl')
    def _check_container_number_unique(self):
        for number in self:
            if not number.is_unique_container_number():
                raise ValidationError(_('Container number should be unique and not used on other shipments.'))

    def is_unique_container_number(self):
        self.ensure_one()

        if not self.container_number:
            return True
        if self.shipment_id.carrier_booking_container_ids.container_number_ids.mapped('container_number').count(self.container_number) > 1:
            return False

        containers = self.search([
            ('container_number', '=', self.container_number)
        ])
        active_container = containers.filtered(lambda container: any(master_cnt.shipment_id.state not in ('cancelled') for master_cnt in containers.mapped('package_ids')) or any(
            house_cnt.shipment_id.state not in ('cancelled') for house_cnt in containers.mapped('house_shipment_package_ids')))
        return len(active_container) <= 1
