# -*- coding: utf-8 -*-
from odoo import models, fields, _
from ..models import freight_service_job
from odoo.exceptions import ValidationError

STATE = [(key, value) for key, value in freight_service_job.SERVICE_JOB_STATE]


class WizardServiceJobStatus(models.TransientModel):
    _name = 'wizard.service.job.status'
    _description = 'Wizard Service Job Status'

    service_job_id = fields.Many2one('freight.service.job')
    change_reason_id = fields.Many2one('shipment.change.reason', string='Reason')
    state = fields.Selection(STATE, store=True)
    remark = fields.Text(string='Remarks')

    def action_change_status(self):
        self.ensure_one()
        state = self.state
        service_job = self.service_job_id
        if not service_job or service_job.state == state:
            return True
        message = ''

        if state == 'completed':
            required_fields = ''''''
            if not service_job.origin_port_un_location_id:
                required_fields += '\n - Origin Port'
            if not service_job.destination_port_un_location_id:
                required_fields += '\n - Destination Port'
            if required_fields:
                raise ValidationError(_('Invalid Fields \n %s') % (required_fields))

        if service_job.state in ['cancelled', 'completed'] and not self.env.user.has_group('freight_management.group_allow_status_change_of_completed_shipment'):
            raise ValidationError(_('You can not change status of %s service job.') % (service_job.state))

        if self.change_reason_id:
            message = 'Service Job state changed to <strong>"%s"</strong> due to <strong>%s</strong><br/>' % (state, self.change_reason_id.name)
        if self.remark:
            message = 'Service Job state changed to <strong>"%s"</strong> due to <strong>%s</strong><br/>' % (state, self.remark)
        vals = {'state': state}
        service_job.write(vals)
        if message:
            service_job.message_post(body=_(message))
