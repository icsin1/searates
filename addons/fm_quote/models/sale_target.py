
from odoo import models, fields


class CRMSaletarget(models.Model):
    _inherit = "crm.sale.target"

    def _get_target_parameter(self):
        result = super()._get_target_parameter()
        result.extend([('quotation', 'Quotation'),])
        return result

    non_fcl_target_parameter = fields.Selection(_get_target_parameter, compute='_compute_non_fcl_target_parameter', inverse='_inverse_non_fcl_target_parameter')

    def get_excel_report_field_name(self):
        if self.target_parameter == 'quotation':
            return ['period', 'shipment_quotation_name', 'target_parameter', 'target_value', 'target_uom_id', 'actual_value']
        return super().get_excel_report_field_name()
