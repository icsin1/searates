# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from ..models import freight_master_shipment
from odoo.exceptions import ValidationError

AIR_STATE = [(key, value) for key, value in freight_master_shipment.MASTER_STATE if key not in ['booked']]


class WizardMasterShipmentStatus(models.TransientModel):
    _name = 'wizard.master.shipment.status'
    _description = 'Wizard Master Shipment Status'

    @api.model
    def _default_allow_status_change(self):
        shipment_id = self.env.context.get('default_shipment_id', False)
        if shipment_id:
            shipment = self.env['freight.master.shipment'].search([
                ('id', '=', shipment_id),
            ])
            if self.env.user.has_group('freight_management.group_allow_status_change_of_completed_shipment') and shipment.state in ['cancelled', 'completed']:
                return True
            else:
                return False
        return False

    shipment_id = fields.Many2one('freight.master.shipment', string='Shipment')
    mode_type = fields.Selection(related='shipment_id.mode_type')
    change_reason_id = fields.Many2one('shipment.change.reason', string='Reason')
    state = fields.Selection(freight_master_shipment.MASTER_STATE, required=False)
    air_state = fields.Selection(AIR_STATE)
    remark = fields.Text(string='Remarks')
    allow_status_change = fields.Boolean(default=_default_allow_status_change)
    reason = fields.Text(string="Reason")

    @api.onchange('air_state')
    def _onchange_air_state(self):
        for wizard in self:
            wizard.state = wizard.air_state

    def action_change_status(self):
        self.ensure_one()
        shipment = self.shipment_id
        state = self.state
        if self.mode_type == 'air':
            state = self.air_state
        if not shipment or shipment.state == state:
            return True
        message = ''

        if self.state not in ['draft', 'cancelled']:
            required_fields = ''''''
            if not shipment.etd_time and shipment.mode_type != 'land' and not shipment.is_courier_shipment:
                required_fields += '\n - ETD'
            if not shipment.eta_time and shipment.mode_type != 'land' and not shipment.is_courier_shipment:
                required_fields += '\n - ETA'
            if not shipment.origin_port_un_location_id and shipment.mode_type != 'land':
                required_fields += '\n - Origin Port'
            if not shipment.destination_port_un_location_id and shipment.mode_type != 'land':
                required_fields += '\n - Destination Port'
            if required_fields:
                raise ValidationError(_('Invalid Fields \n %s') %(required_fields))

        if shipment.state in ['cancelled', 'completed'] and not self.env.user.has_group('freight_management.group_allow_status_change_of_completed_shipment'):
            raise ValidationError(_('You can not change status of %s Shipment.') % (shipment.state))

        if state not in ['draft', 'cancelled'] and not shipment.pack_unit and not shipment.cargo_is_package_group:
            raise ValidationError(_('Please enter packs value.'))

        if state in ['cancelled']:
            containers = shipment.mapped('container_ids')
            if containers:
                containers.write({'container_number': False})

        if self.change_reason_id:
            message = 'Shipment state changed to <strong>"%s"</strong> due to <strong>%s</strong><br/>' % (state, self.change_reason_id.name)
        if self.remark:
            message = '%sRemarks: %s<br/>' % (message, self.remark)
        if self.reason:
            message = 'Shipment state changed to <strong>"%s"</strong> due to <strong>%s</strong><br/>' % (state, self.reason)
        vals = {'state': state}
        shipment.write(vals)
        if message:
            shipment.message_post(body=_(message))
