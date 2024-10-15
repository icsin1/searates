# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    party_types = fields.Boolean('Enable Party Types for Master Shipment', config_parameter='freight_management.party_types')
    module_ics_cargoesflow = fields.Boolean(default=False, string='Shipment / Container Tracking')
    module_fm_house_shipment_from_master = fields.Boolean(default=False, string='House Shipment From Master')
    enable_disable_part_bl = fields.Boolean(string="Enable Part BL", related='company_id.enable_disable_part_bl', readonly=False)
    module_freight_management_export_import = fields.Boolean(default=False, string='Enable Export To Import')
    enable_disable_reexport_hs = fields.Boolean(string="Enable ReExport Shipment", related='company_id.enable_disable_reexport_hs', readonly=False)
    charge_migration = fields.Boolean('Enable Charge Master Migration', config_parameter='freight_management.charge_migration')
    enable_cut_off_dates = fields.Boolean(related="company_id.enable_cut_off_dates", readonly=False)
    enable_feeder_details = fields.Boolean(related="company_id.enable_feeder_details", readonly=False)
    enable_disable_shipping_line = fields.Boolean(string="Enable Scac Prefix Code", related='company_id.enable_disable_shipping_line', readonly=False)
    enable_non_mandatory_fields = fields.Boolean('Enable Non-Mandatory Fields in Opportunity,Quote,House &amp; Master', config_parameter='freight_management.enable_non_mandatory_fields')
    allow_edit_external_carrier_bookings = fields.Boolean('Allow edit of External Carrier Bookings', related='company_id.allow_edit_external_carrier_bookings', readonly=False)
    shipper_consignee_non_mandatory = fields.Boolean('Enable Shipper and Consignee are Non Mandatory', config_parameter='freight_management.shipper_consignee_non_mandatory')
    shipment_status_change = fields.Boolean(string="Shipment Status Change", related='company_id.shipment_status_change', readonly=False)
    container_basic_validation = fields.Boolean('Enable Container Length Validation (Without ISO Standard)', config_parameter='freight_management.container_basic_validation')
    module_fm_container_validation = fields.Boolean(default=False, string="Enable Container Validation (Including ISO6346 format Check)")
