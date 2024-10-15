from odoo import models, api


class TariffServiceWizardLine(models.TransientModel):
    _inherit = 'tariff.service.line.wizard'

    @api.onchange('measurement_basis_id')
    def _onchange_measurement_basis_id(self):
        """
        Updating number of units based on Quote for and packs
        """
        res = super(TariffServiceWizardLine, self)._onchange_measurement_basis_id()
        for line in self:
            wiz_rec = line.tariff_service_wiz_id
            record = wiz_rec.get_record()
            unit_measurement_basis = self.env.ref('fm_service_job.measurement_basis_unit', raise_if_not_found=False)
            if line.measurement_basis_id == unit_measurement_basis:
                if record.pack_unit:
                    line.quantity = record.pack_unit or 1
        return res
