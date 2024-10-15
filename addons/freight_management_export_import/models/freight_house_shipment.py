import json
from lxml import etree
from odoo import models, fields, api, _


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    enable_import_button = fields.Boolean(compute='_compute_enable_import', store=True)
    shipment_import_id = fields.Many2one('freight.house.shipment', string='Import Shipment', copy=False)
    export_shipment_id = fields.Many2one('freight.house.shipment', string='Export Shipment', copy=False)
    import_company_id = fields.Many2one('res.company', string='Import Company', copy=False, domain=lambda self: [
        ('id', 'in', self.env.user.company_ids.filtered(lambda company: company.id != self.env.company.id).ids)])

    @api.depends('state', 'shipment_import_id')
    def _compute_enable_import(self):
        export_shipment_type = self.env.ref('freight_base.shipment_type_export')
        for rec in self:
            rec.enable_import_button = False
            if rec.state == 'completed' and rec.shipment_type_id.id == export_shipment_type.id:
                rec.enable_import_button = True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' and self.env.user.has_group('freight_management_export_import.access_export_to_import'):
            form_view_id = self.env['ir.model.data']._xmlid_to_res_id('freight_management.freight_house_shipment_view_form')
            if res.get('view_id') == form_view_id:
                doc = etree.XML(res['arch'])
                if doc.xpath("//field[@name='import_company_id']"):
                    for node in doc.xpath("//field[@name='import_company_id']"):
                        modifiers = json.loads(node.get("modifiers"))
                        modifiers['readonly'] = [['export_shipment_id', '!=', False]]
                        node.set('modifiers', json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc)
        return res

    def action_create_import_shipment(self):
        self.ensure_one()
        import_house_vals = {
            'company_id': self.import_company_id.id,
            'shipment_import_id': self.id,
            'tag_ids': [(6, 0, self.tag_ids.ids)],
            'shipment_type_id': self.env.ref('freight_base.shipment_type_import').id,
            'pack_unit': self.pack_unit,
            'pack_unit_uom_id': self.pack_unit_uom_id.id,
            'gross_weight_unit': self.gross_weight_unit,
            'gross_weight_unit_uom_id': self.gross_weight_unit_uom_id.id,
            'volume_unit': self.volume_unit,
            'volume_unit_uom_id': self.volume_unit_uom_id.id,
            'net_weight_unit': self.net_weight_unit,
            'net_weight_unit_uom_id': self.net_weight_unit_uom_id.id,
            'weight_volume_unit': self.weight_volume_unit,
            'weight_volume_unit_uom_id': self.weight_volume_unit_uom_id.id,
            'voyage_number': self.voyage_number,
            'vessel_id': self.vessel_id.id,
            'shipping_line_id': self.shipping_line_id.id,
            'lc_number': self.lc_number,
            'commercial_invoice': self.commercial_invoice,
            'customs_document_ids': [(0, 0, document.copy_data()[0]) for document in self.customs_document_ids],
            'container_ids': [(0, 0, container.copy_data()[0]) for container in self.container_ids],
            'aircraft_type': self.aircraft_type,
            'handling_info': self.handling_info,
            'iata_code': self.iata_code,
            'commodity': self.commodity,
            'declared_value_carrier': self.declared_value_carrier,
            'declared_value_customer': self.declared_value_customer,
            'accounting_info': self.accounting_info,
            'package_ids': [(0, 0, package.copy_data()[0]) for package in self.package_ids],
            'transportation_detail_ids': [(0, 0, transport.copy_data()[0]) for transport in self.transportation_detail_ids],
        }
        import_shipment_id = self.sudo().copy(import_house_vals)
        self.export_shipment_id = import_shipment_id.id
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'warning',
                'message': _("Import Shipment has been created successfully: {}".format(import_shipment_id.display_name)),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
