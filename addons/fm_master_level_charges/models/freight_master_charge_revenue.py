
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MasterShipmentChargeRevenue(models.Model):
    _inherit = 'master.shipment.charge.revenue'

    @api.depends('master_shipment_id.house_shipment_ids')
    def _compute_attached_house_shipment_ids(self):
        for charge in self:
            charge.attached_house_shipment_ids = charge.master_shipment_id.house_shipment_ids.ids

    attached_house_shipment_ids = fields.Many2many('freight.house.shipment',
                                                   compute="_compute_attached_house_shipment_ids",
                                                   store=True)
    house_shipment_id = fields.Many2one('freight.house.shipment', string="House Shipment")

    def detach_charge_from_house_shipment(self):
        self.ensure_one()
        house_charge_billed = self.house_charge_revenue_ids.filtered(
            lambda charge: charge.status in charge._modification_line_restrict_states())
        if house_charge_billed:
            houses = house_charge_billed.mapped('house_shipment_id.name')
            raise ValidationError(
                _('Unable to detach house.\nMasters\'s Charges are already billed or partial billed in below houses.\n\n- {}'.format(
                    '\n- '.join(houses)
                )))
        else:
            self.house_charge_revenue_ids.unlink()

    def _prepare_wizard_adjust_charge_vals(self):
        return {
            'adjust_mode': 'revenue',
            'master_shipment_id': self.master_shipment_id.id,
            'house_shipment_ids': [(6, 0, self.house_shipment_id.ids)],
            'revenue_charge_ids': [(6, 0, self.ids)],
            'line_ids': [(0, 0, {'shipment_id': self.house_shipment_id.id})],
        }

    def attach_charge_to_house_shipment(self):
        self.ensure_one()
        AdjustChargeWizard = self.env['wizard.adjust.charge.with.house']
        charge_wizard_id = AdjustChargeWizard.create(self._prepare_wizard_adjust_charge_vals())
        charge_wizard_id.action_adjust_charges()

    def _get_field_list_to_update_to_house_charges(self):
        return ['charge_description', 'product_id', 'uom_id', 'quantity', 'measurement_basis_id', 'amount_currency_id',
                'amount_rate', 'amount_conversion_rate', 'partner_id', 'partner_address_id']

    def update_attached_charge_to_house_shipment(self, values):
        self.ensure_one()
        house_charge_billed = self.house_charge_revenue_ids.filtered(
            lambda charge: charge.status in charge._modification_line_restrict_states())
        if house_charge_billed:
            houses = house_charge_billed.mapped('house_shipment_id.name')
            raise ValidationError(
                _('Unable to update house.\nMasters\'s Charges are already billed or partial billed in below houses.\n\n- {}'.format(
                    '\n- '.join(houses)
                )))
        else:
            house_charge_values = {}
            field_list_to_update = self._get_field_list_to_update_to_house_charges()
            for key, value in values.items():
                if key in field_list_to_update:
                    house_charge_values[key] = value
            if house_charge_values:
                self.house_charge_revenue_ids.write(house_charge_values)

    @api.model_create_single
    def create(self, values):
        res = super().create(values)
        if 'house_shipment_id' in values and values.get('house_shipment_id'):
            res.attach_charge_to_house_shipment()
        return res

    def write(self, values):
        if 'house_shipment_id' in values and not self._context.get('unlink_house_charge'):
            for charge in self:
                if charge.house_shipment_id:
                    charge.detach_charge_from_house_shipment()
        res = super().write(values)
        for charge in self:
            if 'house_shipment_id' in values and values.get('house_shipment_id'):
                charge.attach_charge_to_house_shipment()
            elif charge.house_shipment_id:
                charge.update_attached_charge_to_house_shipment(values)

        return res
