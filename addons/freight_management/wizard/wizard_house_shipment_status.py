# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ..models import freight_house_shipment

IMPORT_STATE = [(key, value) for key, value in freight_house_shipment.HOUSE_STATE if key not in ['hbl_generated', 'hawb_generated']]
EXPORT_STATE = [(key, value) for key, value in freight_house_shipment.HOUSE_STATE if key not in ['nomination_generated', 'hawb_generated']]
AIR_EXPORT_STATE = [(key, value) for key, value in freight_house_shipment.HOUSE_STATE if key not in ['nomination_generated', 'hbl_generated']]
CROSS_STATE = [(key, value) for key, value in freight_house_shipment.HOUSE_STATE if key not in ['hbl_generated', 'hawb_generated']]
DOMESTIC_EXPORT_STATE = [(key, value) for key, value in freight_house_shipment.HOUSE_STATE if key not in ['nomination_generated', 'hawb_generated']]
REEXPORT_STATE = [(key, value) for key, value in freight_house_shipment.HOUSE_STATE if key not in ['hbl_generated', 'hawb_generated']]


class WizardHouseShipmentStatus(models.TransientModel):
    _name = 'wizard.house.shipment.status'
    _description = 'Wizard House Shipment Status'

    @api.model
    def _default_allow_status_change(self):
        shipment_id = self.env.context.get('default_shipment_id', False)
        if shipment_id:
            shipment = self.env['freight.house.shipment'].search([
                ('id', '=', shipment_id),
            ])
            if self.env.user.has_group('freight_management.group_allow_status_change_of_completed_shipment') and shipment.state in ['cancelled', 'completed']:
                return True
            else:
                return False
        return False

    @api.onchange('shipment_id', 'state')
    def _onchange_detach_master(self):
        for house_state in self:
            house_state.detach_master = True if house_state.state == 'cancelled' and house_state.shipment_id.parent_id and not house_state.shipment_id.is_direct_shipment else False

    shipment_id = fields.Many2one('freight.house.shipment', string='Shipment')
    shipment_type_key = fields.Char(related='shipment_id.shipment_type_key')
    shipment_mode_type = fields.Selection(related='shipment_id.mode_type')
    change_reason_id = fields.Many2one('shipment.change.reason', string='Reason')
    import_state = fields.Selection(IMPORT_STATE)
    export_state = fields.Selection(EXPORT_STATE)
    air_export_state = fields.Selection(AIR_EXPORT_STATE)
    cross_state = fields.Selection(CROSS_STATE)
    domestic_export_state = fields.Selection(DOMESTIC_EXPORT_STATE)
    reexport_state = fields.Selection(REEXPORT_STATE)
    state = fields.Char(compute='_compute_state', store=True)
    remark = fields.Text(string='Remarks')
    detach_master = fields.Boolean('Detach Master')
    is_direct_shipment = fields.Boolean(related='shipment_id.is_direct_shipment', store=True)
    allow_status_change = fields.Boolean(default=_default_allow_status_change)
    reason = fields.Text(string="Reason")

    @api.depends('import_state', 'export_state', 'cross_state', 'shipment_type_key', 'domestic_export_state',
                 'air_export_state', 'reexport_state')
    def _compute_state(self):
        for wizard in self:
            if wizard.shipment_type_key == 'import':
                wizard.state = wizard.import_state
            elif wizard.shipment_type_key == 'export' and wizard.shipment_mode_type == 'air':
                wizard.state = wizard.air_export_state
            elif wizard.shipment_type_key == 'export':
                wizard.state = wizard.export_state
            elif wizard.shipment_type_key == 'cross':
                wizard.state = wizard.cross_state
            elif wizard.shipment_type_key == 'domestic_export':
                wizard.state = wizard.domestic_export_state
            elif wizard.shipment_type_key == 're_export':
                wizard.state = wizard.reexport_state
            else:
                wizard.state = False

    def action_change_status(self):
        self.ensure_one()
        state = self.state
        shipment = self.shipment_id
        if not shipment or shipment.state == state:
            return True
        message = ''

        if self.state not in ['created', 'cancelled']:
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

        if state not in ['created', 'cancelled'] and not shipment.pack_unit and not shipment.cargo_is_package_group:
            raise ValidationError(_('Please enter packs value.'))

        if self.change_reason_id:
            message = 'Shipment state changed to <strong>"%s"</strong> due to <strong>%s</strong><br/>' % (state, self.change_reason_id.name)
        if self.remark:
            message = '%sRemarks: %s<br/>' % (message, self.remark)
        if shipment.parent_id:
            message = '%sMaster Shipment <strong>%s</strong> detached from this Shipment.<br/>' % (message, shipment.parent_id.name)
        if self.reason:
            message = 'Shipment state changed to <strong>"%s"</strong> due to <strong>%s</strong><br/>' % (state, self.reason)
        vals = {'state': state}
        shipment.write(vals)
        if state == 'cancelled' and shipment.parent_id and shipment.is_direct_shipment:
            shipment.parent_id.write({'state': 'cancelled'})
        elif state == 'cancelled' and shipment.parent_id:
            shipment.action_detach_shipment_house()
        if state == 'cancelled':
            house_containers = shipment.mapped('container_ids')
            if house_containers:
                house_containers.write({'container_number': False})
            master_containers = shipment.parent_id.mapped('container_ids')
            if master_containers:
                master_containers.write({'container_number': False})
        if message:
            shipment.message_post(body=_(message))
