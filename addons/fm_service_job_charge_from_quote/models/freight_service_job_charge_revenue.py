from odoo import models, api, _
from odoo.exceptions import ValidationError


class ServiceJobChargeRevenue(models.Model):
    _inherit = 'service.job.charge.revenue'

    @api.model
    def update_revenue_charge_ids(self, service_job_id):
        service_job = self.env['freight.service.job'].browse(int(service_job_id))
        if service_job and not service_job.service_job_quote_id:
            raise ValidationError(_('Service Job-%s is not Generated from Quote.') % (service_job.name))
        service_job.update_revenue_charge_ids()
