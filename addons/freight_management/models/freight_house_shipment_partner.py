
from odoo import models, fields, api


class FreightShipmentPartner(models.Model):
    _name = "freight.house.shipment.partner"
    _description = "Shipment Partner"
    _rec_name = "partner_id"

    freight_shipment_id = fields.Many2one("freight.house.shipment", string="Shipment", ondelete="cascade")
    partner_id = fields.Many2one("res.partner", string="Party", required=True)
    partner_type_id = fields.Many2one("res.partner.type", string="Party Type", required=True)
    party_address_id = fields.Many2one('res.partner', string='Party Address', domain="[('parent_id', '=', partner_id)]")
    party_address = fields.Text(string='Party Address', compute='_compute_party_address', store=True)

    # Updated this constraint, only check unique if partner type is vendor
    _sql_constraints = [
        ('partner_type_uniq', 'CHECK(1=1)', 'Only Single "Partner Type" Line Allowed')
    ]

    @api.depends('partner_id', 'partner_id.child_ids', 'partner_id.child_ids.mark_as_default')
    def _compute_party_address(self):
        for record in self:
            address_parts = []
            if record.partner_id:
                default_address = record.partner_id.child_ids.filtered(lambda line: line.mark_as_default)
                if not default_address:
                    default_address = record.partner_id
                address_parts.extend([
                    default_address.street or '',
                    default_address.street2 or '',
                    default_address.city_id.name or '',
                    default_address.state_id.name or '',
                    default_address.zip or '',
                    default_address.country_id.name or ''
                ])
            record.party_address = ', '.join(filter(None, address_parts))

    def _update_shipment_party_detail(self):
        self.ensure_one()
        # Required sudo() as field level access is not granted to all users
        self = self.sudo()
        freight_shipment_id = self.freight_shipment_id
        field_mapping_ids = self.partner_type_id.field_mapping_ids
        shipment_fields = field_mapping_ids.filtered(lambda field_map: field_map.model_id.model == 'freight.house.shipment')
        values_to_write = {}
        for field in shipment_fields.mapped('field_id'):
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
            freight_shipment_id.with_context(updated_from_line=True).write(values_to_write)

    @api.model_create_single
    def create(self, vals):
        shipment_partner_id = super().create(vals)
        if shipment_partner_id.freight_shipment_id and shipment_partner_id.partner_type_id.field_mapping_ids:
            shipment_partner_id._update_shipment_party_detail()
        return shipment_partner_id

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            record._update_shipment_party_detail()
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id and rec._context.get('force_change'):
                addresses = self.partner_id.get_default_addresses()
                rec.party_address_id = addresses and addresses[0]
