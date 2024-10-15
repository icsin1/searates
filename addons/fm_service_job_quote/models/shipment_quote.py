# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShipmentQuote(models.Model):
    _inherit = 'shipment.quote'

    def get_template_domain(self):
        self.ensure_one()
        if self.quote_for == 'job':
            return json.dumps([('template_for', '=', 'job'), ('service_job_type_id', '=', self.service_job_type_id.id)])
        else:
            return super().get_template_domain()

    @api.depends('quote_for', 'transport_mode_id', 'shipment_type_id', 'cargo_type_id', 'service_job_type_id')
    def _compute_quote_template_domain(self):
        for quote in self:
            quote.quote_template_domain = quote.get_template_domain()

    @api.depends('transport_mode_id', 'shipment_type_id', 'cargo_type_id', 'service_job_type_id')
    def _compute_shipment_quote_template_id(self):
        for quote in self.filtered(lambda q: q.quote_for == 'shipment'):
            shipment_quote_template_id = False
            shipment_quote_template = self.env['shipment.quote.template'].search([
                ('service_job_type_id', '=', quote.service_job_type_id.id),
                ('template_for', '=', 'job'),
            ], order="id desc", limit=1)

            shipment_quote_template_id = shipment_quote_template.id or False
            quote.shipment_quote_template_id = shipment_quote_template_id

    quote_for = fields.Selection(selection_add=[('job', 'Service Job')])
    service_job_type_id = fields.Many2one('freight.job.type', ondelete='restrict', copy=False)
    service_job_ids = fields.One2many('freight.service.job', 'service_job_quote_id')

    @api.onchange('quote_for')
    def _onchange_quote_for(self):
        if self.quote_for == 'job':
            self.update({
                'transport_mode_id': False,
                'shipment_type_id': False,
                'cargo_type_id': False,
            })

    @api.depends('transport_mode_id', 'destination_country_id')
    def _compute_port_of_discharge_domain(self):
        super()._compute_port_of_discharge_domain()
        for rec in self.filtered(lambda quote: quote.quote_for == 'job'):
            domain = []
            if rec.origin_country_id.id:
                domain = [('country_id', '=', rec.destination_country_id.id)]
            rec.port_of_discharge_domain = json.dumps(domain)

    @api.depends('transport_mode_id', 'origin_country_id')
    def _compute_port_of_loading_domain(self):
        super()._compute_port_of_loading_domain()
        for rec in self.filtered(lambda quote: quote.quote_for == 'job'):
            domain = []
            if rec.origin_country_id.id:
                domain = [('country_id', '=', rec.origin_country_id.id)]
            rec.port_of_loading_domain = json.dumps(domain)

    @api.constrains('shipment_quote_template_id', 'quote_for', 'service_job_type_id')
    def _check_service_job_quote_template_id(self):
        for quote in self.filtered(lambda quote: quote.shipment_quote_template_id and quote.quote_for == 'job'):
            if quote.shipment_quote_template_id.service_job_type_id != quote.service_job_type_id:
                raise ValidationError(_("The selected Quote-Template must have the same Service Job Type as the Quote"))

    def _prepare_service_job_vals(self):
        self.ensure_one()
        default_service_job_vals = {
            'default_service_job_quote_id': self.id,
            'default_company_id': self.company_id.id,
            'default_date': self.date,
            'default_client_id': self.client_id.id,
            'default_client_address_id': self.client_address_id.id,
            'default_shipper_id': self.shipper_id.id,
            'default_shipper_address_id': self.shipper_address_id.id,
            'default_consignee_id': self.consignee_id.id,
            'default_consignee_address_id': self.consignee_address_id.id,
            'default_pack_unit': self.pack_unit,
            'default_pack_unit_uom_id': self.pack_unit_uom_id.id,
            'default_gross_weight_unit': self.gross_weight_unit,
            'default_gross_weight_unit_uom_id': self.gross_weight_unit_uom_id.id,
            'default_volume_unit': self.volume_unit,
            'default_volume_unit_uom_id': self.volume_unit_uom_id.id,
            'default_net_weight_unit': self.net_weight_unit,
            'default_net_weight_unit_uom_id': self.net_weight_unit_uom_id.id,
            'default_weight_volume_unit': self.weight_volume_unit,
            'default_weight_volume_unit_uom_id': self.weight_volume_unit_uom_id.id,
            'default_origin_port_un_location_id': self.port_of_loading_id.id,
            'default_destination_port_un_location_id': self.port_of_discharge_id.id,
            'default_ownership_id': self.client_id.id,
            'default_origin_un_location_id': self.origin_un_location_id.id,
            'default_destination_un_location_id': self.destination_un_location_id.id,
            'default_is_hazardous': self.is_dangerous_good,
            'default_haz_class_id': self.haz_class_id and self.haz_class_id.id or False,
            'default_haz_un_number': self.haz_un_number or False,
            'default_haz_remark': self.dangerous_good_note,
            'default_sales_agent_id': self.user_id.id,
            'default_service_job_type_id': self.service_job_type_id.id,
            'default_remarks': self.remarks,
        }
        return default_service_job_vals

    def action_create_service_job(self):
        self.ensure_one()
        return {
            'name': 'Service Job',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.service.job',
            'context': self._prepare_service_job_vals(),
        }

    def action_open_service_job(self):
        return_vals = {
            'name': _('Service Job'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.service.job',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', self.service_job_ids.ids)],
            'context': {'create': False}
        }
        if len(self.service_job_ids.ids) == 1:
            return_vals.update({
                'view_mode': 'form',
                'res_id': self.service_job_ids.ids[0],
                'domain': [('id', '=', self.service_job_ids[0].id)],
            })
        return return_vals

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('update_freight_sequence_dynamic'):
            field_name_lst = ['service_job_type_id']
            for rec in self.filtered(lambda quote: quote.quote_for == 'job'):
                rec.update_shipment_quote_sequence(vals, field_name_lst)
        return res


class ShipmentQuoteLine(models.Model):
    _inherit = "shipment.quote.line"

    def get_charge_domain(self):
        self.ensure_one()
        if self.quotation_id and self.quotation_id.quote_for == 'job':
            charge_category = self.env.ref('fm_service_job.job_charge_category', raise_if_not_found=False)
            domain = ["|", ("company_id", "=", self.company_id.id), ("company_id", "=", False)]
            if charge_category:
                domain.append(("categ_id", "=", charge_category.id))
            return json.dumps(domain)
        else:
            return super().get_charge_domain()

    @api.onchange('measurement_basis_id', 'container_type_id')
    def onchange_for_measurement_basis_unit(self):
        """
        Updating number of units based on Quote for and packs
        """
        if self.quotation_id.quote_for == 'job':
            unit_charges_measure_dict = {
                self.env.ref('fm_service_job.measurement_basis_unit', raise_if_not_found=False): 'pack_unit',
            }
            if self.measurement_basis_id and self.quotation_id:
                column_unit = unit_charges_measure_dict.get(self.measurement_basis_id)
                self.quantity = self.quotation_id[column_unit] if self.quotation_id[column_unit] else 1
