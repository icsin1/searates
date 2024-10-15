from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class WizardAdjustChargesWithHouses(models.TransientModel):
    _name = 'wizard.adjust.charge.with.house'
    _description = 'Charge Adjustment with Houses'

    adjust_mode = fields.Selection([('cost', 'Cost'), ('revenue', 'Revenue')], default='cost', required=True)
    master_shipment_id = fields.Many2one('freight.master.shipment')
    house_shipment_ids = fields.Many2many('freight.house.shipment')
    revenue_charge_ids = fields.Many2many('master.shipment.charge.revenue', 'master_charge_revenue_adjust_rel', 'wizard_id', 'charge_id')
    cost_charge_ids = fields.Many2many('master.shipment.charge.cost', 'master_charge_cost_adjust_rel', 'wizard_id', 'charge_id')
    line_ids = fields.One2many('wizard.adjust.charge.line', 'adjust_line_id')
    cargo_is_package_group = fields.Boolean(related='master_shipment_id.cargo_is_package_group', store=True)
    measurement_basis_id = fields.Many2one('freight.measurement.basis', string='Measurement Basis', compute="_compute_measurement_basis_id")
    measure_container_type_id = fields.Many2one('freight.container.type')

    @api.depends('adjust_mode', 'revenue_charge_ids', 'cost_charge_ids')
    def _compute_measurement_basis_id(self):
        for rec in self:
            rec.measurement_basis_id = rec[f'{rec.adjust_mode}_charge_ids'][0].mapped('measurement_basis_id').id

    def _validate_charges(self):
        """ Before adjusting charges to house, validating already invoiced/billed lines
        """
        self.ensure_one()
        house_charges_ids = self[f'{self.adjust_mode}_charge_ids'].mapped(f'house_charge_{self.adjust_mode}_ids')
        invoiced_house_charges = house_charges_ids.filtered(lambda charge: charge.status in charge._modification_line_restrict_states())

        if invoiced_house_charges:
            invoice_charges_msg = []
            if self.adjust_mode == 'cost':
                selected_house_shipment_charges = self.line_ids.mapped('shipment_id.cost_charge_ids')
            else:
                selected_house_shipment_charges = self.line_ids.mapped('shipment_id.revenue_charge_ids')
            for selected_house_charge in selected_house_shipment_charges:
                if selected_house_charge.id in invoiced_house_charges.ids:
                    invoice_charges_msg.append(f"- {selected_house_charge.product_id.display_name} of {selected_house_charge.house_shipment_id.name}")

            if invoice_charges_msg:
                msg = _("Following charges cannot be adjusted as Invoice/Bill has already been generated:")
                msg += '\n'.join(invoice_charges_msg)
                raise UserError(_(msg))

    def action_adjust_charges(self):
        self.ensure_one()

        # If adjustment ratio all line is zero
        if not sum(self.line_ids.mapped('adjusted_amount')):
            raise UserError(_("Nothing to Adjust"))

        charges = self.revenue_charge_ids or self.cost_charge_ids
        wrong_adjustment_charge = charges.filtered(lambda c: c.quantity != sum(self.line_ids.mapped('ratio_value')))
        if wrong_adjustment_charge:
            raise ValidationError(_("'No of unit' of %s to adjust must be equal 'House value' of all Adjustment House Shipment.") % (wrong_adjustment_charge[0].charge_description))

        for adjust_charge in self.line_ids:
            self._validate_charges()
            # Removing existing master shipment charges
            house_shipment = adjust_charge.shipment_id
            charges = house_shipment.cost_charge_ids if self.adjust_mode == 'cost' else house_shipment.revenue_charge_ids
            if self.adjust_mode == 'cost':
                existing_charges = charges.filtered(
                    lambda charge: charge.master_shipment_cost_charge_id.id in self.cost_charge_ids.ids
                )
                existing_charges.unlink()
            else:
                existing_charges = charges.filtered(
                    lambda charge: charge.master_shipment_revenue_charge_id.id in self.revenue_charge_ids.ids
                )
                existing_charges.unlink()

            # Creating new charges
            charges = []
            adjustment_ratio = adjust_charge._get_adjustment_ratio()
            to_adjust_charges = self.cost_charge_ids if self.adjust_mode == 'cost' else self.revenue_charge_ids
            for charge in to_adjust_charges:
                partner_id = adjust_charge.shipment_id.client_id.id
                partner_address_id = adjust_charge.shipment_id.client_address_id.id
                charges.append((0, 0, {
                    'master_shipment_{}_charge_id'.format(self.adjust_mode): charge.id,
                    'charge_description': "{} - {} - {}".format('M', self.master_shipment_id.name, charge.product_id.name),
                    'product_id': charge.product_id.id,
                    'uom_id': charge.product_id.uom_id.id,
                    'quantity': round(charge.quantity * adjustment_ratio, 2),
                    'measurement_basis_id': charge.measurement_basis_id.id,
                    'container_type_id': charge.container_type_id.id,
                    'amount_currency_id': charge.amount_currency_id.id,
                    'amount_rate': charge.amount_rate,
                    'amount_conversion_rate': charge.amount_conversion_rate,
                    'partner_id': partner_id if self.adjust_mode == 'revenue' else charge.partner_id.id,
                    'partner_address_id': partner_address_id if self.adjust_mode == 'revenue' else charge.partner_address_id.id,
                    'remarks': _('Adjusted from Master shipment {} at ratio {}'.format(self.master_shipment_id.name, round(adjustment_ratio, 3)))
                }))
            adjust_charge.shipment_id.write({f'{self.adjust_mode}_charge_ids': charges})
            to_adjust_charges.write({'status': 'adjusted'})
        house_shipments = self.line_ids.mapped('shipment_id')
        house_shipment_names = house_shipments.mapped('name')
        if house_shipments:
            house_shipments[0].notify_user(_('Charges Adjusted'), _('Charges Adjusted to {}'.format(','.join(house_shipment_names))), 'success')
        else:
            raise UserError(_("No house shipment found, Please attach a house shipment to the master shipment."))


class WizardAdjustChargesWithHouseLine(models.TransientModel):
    _name = 'wizard.adjust.charge.line'
    _description = 'Adjustment Line'

    @api.depends('shipment_id', 'adjust_line_id.measurement_basis_id')
    def _compute_ratio_value(self):
        shipment_measurement = self.env.ref('freight_base.measurement_basis_shipment')
        container_count_measurement = self.env.ref('freight_base.measurement_basis_container_count')
        container_type_measurement = self.env.ref('freight_base.measurement_basis_container_type')
        weight_measurement = self.env.ref('freight_base.measurement_basis_weight')
        volume_measurement = self.env.ref('freight_base.measurement_basis_volume')
        chargeable_measurement = self.env.ref('freight_base.measurement_basis_chargeable')
        teu_measurement = self.env.ref('freight_base.measurement_basis_teu')
        adjust_measurement = self.adjust_line_id.measurement_basis_id
        for line in self:
            if adjust_measurement == weight_measurement:
                weight_uom = self.env.company.weight_uom_id
                value = line.shipment_id.gross_weight_unit
                weight_uom = line.shipment_id.gross_weight_unit_uom_id
                if weight_uom and weight_uom.id != weight_uom.id:
                    value = weight_uom._compute_quantity(value, weight_uom)
                line.ratio_value = value
            elif adjust_measurement == volume_measurement:
                cbm_uom = self.env.company.volume_uom_id
                value = line.shipment_id.volume_unit
                volume_uom = line.shipment_id.volume_unit_uom_id
                if volume_uom and volume_uom.id != cbm_uom.id:
                    value = volume_uom._compute_quantity(value, cbm_uom)
                line.ratio_value = value
            elif adjust_measurement == chargeable_measurement:
                line.ratio_value = line.shipment_id.chargeable_kg
            elif adjust_measurement == shipment_measurement:
                line.ratio_value = len(line.shipment_id)
            elif adjust_measurement == teu_measurement:
                # Getting each house TEU total
                line.ratio_value = sum(line.shipment_id.container_ids.mapped('no_of_teu'))
            elif adjust_measurement == container_count_measurement:
                line.ratio_value = len(line.shipment_id.container_ids)
            elif adjust_measurement == container_type_measurement:
                container_type = self.adjust_line_id.measure_container_type_id
                containers = line.shipment_id.container_ids
                line.ratio_value = len(containers.filtered(lambda c: c.container_type_id == container_type))

    adjust_line_id = fields.Many2one('wizard.adjust.charge.with.house', ondelete='cascade')
    master_shipment_id = fields.Many2one(related='adjust_line_id.master_shipment_id')
    shipment_id = fields.Many2one('freight.house.shipment', readonly=True, domain="[('parent_id', '=', master_shipment_id)]")
    adjustment_ratio = fields.Float(compute='_compute_adjustment_ratio', store=True, readonly=False)
    currency_id = fields.Many2one('res.currency', related='master_shipment_id.currency_id', store=True)
    adjusted_amount = fields.Monetary(compute="_compute_adjusted_amount")
    ratio_value = fields.Float("House Value", compute="_compute_ratio_value", store=True)

    @api.constrains('adjustment_ratio')
    @api.onchange('adjustment_ratio')
    def _check_adjustment_ration(self):
        for rec in self:
            if rec.adjustment_ratio < 0:
                raise UserError(_('Adjustment ration can not be less than zero.'))

    def _get_adjustment_ratio(self):
        self.ensure_one()
        total_adjustment_ratio = sum(self.adjust_line_id.line_ids.mapped('adjustment_ratio')) or 1
        return self.adjustment_ratio / total_adjustment_ratio

    @api.depends('adjust_line_id', 'ratio_value', 'adjust_line_id.measurement_basis_id', 'adjust_line_id.line_ids')
    def _compute_adjustment_ratio(self):
        shipment_measurement = self.env.ref('freight_base.measurement_basis_shipment')
        container_count_measurement = self.env.ref('freight_base.measurement_basis_container_count')
        teu_measurement = self.env.ref('freight_base.measurement_basis_teu')
        container_type_measurement = self.env.ref('freight_base.measurement_basis_container_type')
        for line in self:
            total_value = sum(line.adjust_line_id.mapped('line_ids.ratio_value'))
            if line.adjust_line_id.measurement_basis_id in [shipment_measurement, container_count_measurement, teu_measurement, container_type_measurement]:
                line.adjustment_ratio = line.ratio_value
            else:
                line.adjustment_ratio = round((line.ratio_value / total_value), 2) if total_value else 1

    @api.depends('adjust_line_id.cost_charge_ids', 'adjust_line_id.revenue_charge_ids', 'adjustment_ratio')
    def _compute_adjusted_amount(self):
        for rec in self:
            charges = rec.adjust_line_id.cost_charge_ids if rec.adjust_line_id.adjust_mode == 'cost' else rec.adjust_line_id.revenue_charge_ids
            total_amount = sum(charges.mapped('total_amount'))
            ratio_total = sum(rec.adjust_line_id.line_ids.mapped('adjustment_ratio')) or 1
            ratio = (rec.adjustment_ratio / ratio_total) or 1
            rec.adjusted_amount = 0 if rec.adjustment_ratio == 0.00 else round(total_amount * ratio, 3)
