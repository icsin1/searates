from odoo import models

from odoo.addons.freight_management_charges.models import mixin_freight_charge

mixin_freight_charge.model_dict.update({
    'service.job.charge.cost': 'freight.service.job',
    'service.job.charge.revenue': 'freight.service.job',
})


class FreightChargeMixin(models.AbstractModel):
    _inherit = 'mixin.freight.charge'

    def get_service_job_model(self):
        return ['freight.service.job']

    def get_cost_models(self):
        result = super().get_cost_models()
        result.append('service.job.charge.cost')
        return result

    def get_revenue_models(self):
        result = super().get_revenue_models()
        result.append('service.job.charge.revenue')
        return result

    def get_model_field_name(self, model):
        if model in ['service.job.charge.cost', 'service.job.charge.revenue']:
            return 'service_job_id'
        return super().get_model_field_name(model)

    def get_measurement_basis_domain(self, record):
        if record._name in self.get_service_job_model():
            return [('is_job_measurement', '=', True)]
        else:
            return super().get_measurement_basis_domain(record)

    def get_charge_domain(self, record):
        if record._name in self.get_service_job_model():
            return [('categ_id', '=', self.env.ref('fm_service_job.job_charge_category').id)]
        else:
            return super().get_charge_domain(record)

    def action_option_from_view(self):
        if self._name in ['service.job.charge.revenue', 'service.job.charge.cost']:
            return {
                'name': self.name,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': self._name,
                'res_id': self.id,
                'context': {'from_copy_method': True, **self._context,
                            'edit': self.service_job_id.state not in ['cancelled'] if not self.env.user.has_group('freight_management.group_super_admin') else True
                            },
                }
        else:
            return super().action_option_from_view()
