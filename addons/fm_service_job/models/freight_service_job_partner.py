
from odoo import models, fields, api


class FreightServiceJobPartner(models.Model):
    _name = "freight.service.job.partner"
    _description = "Service Job Partner"
    _rec_name = "partner_id"

    service_job_id = fields.Many2one("freight.service.job", string="Service Job", ondelete="cascade")
    partner_id = fields.Many2one("res.partner", string="Party", required=True)
    partner_type_id = fields.Many2one("res.partner.type", string="Party Type", required=True)
    party_address_id = fields.Many2one('res.partner', string='Party Address', domain="[('parent_id', '=', partner_id)]")

    def _update_service_job_party_detail(self):
        self.ensure_one()
        # Required sudo() as field level access is not granted to all users
        self = self.sudo()
        service_job_id = self.service_job_id
        field_mapping_ids = self.partner_type_id.field_mapping_ids
        service_job_fields = field_mapping_ids.filtered(lambda field_map: field_map.model_id.model == 'freight.service.job')
        values_to_write = {}
        for field in service_job_fields.mapped('field_id'):
            values_to_write[field.name] = self.partner_id.id
        if self.partner_type_id.id == self.env.ref('freight_base.org_type_customer').id:
            values_to_write['client_id'] = self.partner_id.id
            values_to_write['client_address_id'] = self.party_address_id.id
        if self.partner_type_id.id == self.env.ref('freight_base.org_type_shipper').id:
            values_to_write['shipper_id'] = self.partner_id.id
            values_to_write['shipper_address_id'] = self.party_address_id.id
        if self.partner_type_id.id == self.env.ref('freight_base.org_type_consignee').id:
            values_to_write['consignee_id'] = self.partner_id.id
            values_to_write['consignee_address_id'] = self.party_address_id.id
        if values_to_write:
            service_job_id.with_context(updated_from_line=True).write(values_to_write)

    @api.model_create_single
    def create(self, vals):
        service_job_partner_id = super().create(vals)
        if service_job_partner_id.service_job_id and service_job_partner_id.partner_type_id.field_mapping_ids:
            service_job_partner_id._update_service_job_party_detail()
        return service_job_partner_id

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            record._update_service_job_party_detail()
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id and rec._context.get('force_change'):
                addresses = self.partner_id.get_default_addresses()
                rec.party_address_id = addresses and addresses[0]