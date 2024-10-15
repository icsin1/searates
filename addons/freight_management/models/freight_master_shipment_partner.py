import json
from odoo import models, fields, api


class FreightMasterShipmentPartner(models.Model):
    _name = "freight.master.shipment.partner"
    _description = "Master Shipment Partner"
    _rec_name = "partner_id"

    @api.depends('freight_shipment_id.mode_type', 'partner_type_id', 'freight_shipment_id')
    def _compute_party_type_domain(self):
        is_party_type = self.env['ir.config_parameter'].sudo().get_param('freight_management.party_types')
        for rec in self:
            party_code = ['destination_agent']
            party_type_id = []
            if is_party_type and rec.freight_shipment_id.mode_type in ('air', 'sea'):
                party_code.extend(['shipper', 'consignee'])
                party_type_id = [
                    self.env.ref('freight_base.org_type_notify_1').id,
                    self.env.ref('freight_base.org_type_co_loader').id,
                    self.env.ref('freight_base.org_type_customer').id,
                    self.env.ref('freight_base.org_type_issuing_carrier_agent').id,
                ]
            domain = ['|', ('code', 'in', party_code), ('id', 'in', party_type_id)]
            rec.party_type_domain = json.dumps(domain)

    freight_shipment_id = fields.Many2one("freight.master.shipment", string="Shipment", ondelete="cascade")
    partner_id = fields.Many2one("res.partner", string="Party", required=True)
    partner_type_id = fields.Many2one("res.partner.type", string="Party Type", required=True)
    party_address_id = fields.Many2one('res.partner', string='Party Address', domain="['|', ('parent_id', '=', partner_id), ('id', '=', partner_id)]")
    party_type_domain = fields.Char(compute='_compute_party_type_domain', store=True)
    party_address = fields.Text(string='Party Address', compute='_compute_party_address', store=True)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id and rec._context.get('force_change'):
                addresses = self.partner_id.get_default_addresses()
                rec.party_address_id = addresses and addresses[0]

    @api.onchange('partner_type_id')
    def _onchange_partner_type_id(self):
        if self.freight_shipment_id.mode_type == 'air':
            self.update({
                'partner_id': False,
                'party_address_id': False
            })

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
