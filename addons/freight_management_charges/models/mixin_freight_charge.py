import base64
import io
import xlsxwriter

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

model_dict = {
    'house.shipment.charge.revenue': 'freight.house.shipment',
    'house.shipment.charge.cost': 'freight.house.shipment',
    'master.shipment.charge.revenue': 'freight.master.shipment',
    'master.shipment.charge.cost': 'freight.master.shipment'
}


class FreightChargeMixin(models.AbstractModel):
    _name = 'mixin.freight.charge'
    _inherit = ['mail.thread']
    _description = 'Freight Charge Mixin'
    _rec_name = 'name'

    def _default_sequence(self):
        sequence = self.search([], limit=1, order="sequence DESC").sequence or 0
        return sequence + 1

    name = fields.Char(compute='_compute_name', store=True)
    sequence = fields.Integer(string='Sequence', default=_default_sequence)
    product_id = fields.Many2one('product.product', string='Charge Details', required=True, tracking=True,
                                 domain=lambda self: "['|', ('company_id', '=', company_id), ('company_id', '=', False), \
                                                                     ('categ_id', '=', %s)]" % self.env.ref(
                                     'freight_base.shipment_charge_category').id)
    charge_description = fields.Char(string='Charge Description', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Local Currency', tracking=True)
    uom_id = fields.Many2one('uom.uom', related="product_id.uom_id", string='UoM', store=True)
    quantity = fields.Float(string='No of Units', default=1, required=True, tracking=True, group_operator=False)
    measurement_basis_id = fields.Many2one('freight.measurement.basis', string='Measurement Basis', required=True, tracking=True)

    # Container Type based Measurement Basis
    is_container_type_basis = fields.Boolean(compute='_compute_is_container_type_basis')
    container_type_id = fields.Many2one('freight.container.type', string='Container Type')

    # Amount
    amount_currency_id = fields.Many2one('res.currency', string='Currency', required=True, tracking=True)
    amount_conversion_rate = fields.Float(string='Exchange Rate', default=1, tracking=True, required=True, digits='Currency Exchange Rate', group_operator=False)
    amount_rate = fields.Monetary(string='Rate per Unit', currency_field='amount_currency_id', tracking=True, required=True, group_operator=False)
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True, required=True, domain="[('type', '=', 'contact')]")
    partner_address_id = fields.Many2one('res.partner', string='Partner Address', domain="[('parent_id', '=', partner_id), ('type', '=', 'invoice')]", tracking=True)
    remarks = fields.Text(string='Remarks', tracking=True)
    amount_currency_mismatch = fields.Boolean(compute='_compute_amount_currency_mismatch', tracking=True, store=True)
    total_currency_amount = fields.Monetary(string='Total Amount', compute='_compute_total_currency_amount', inverse="_inverse_total_currency_amount",
                                            currency_field='amount_currency_id', store=True, tracking=True, group_operator=False, readonly=False)
    total_amount = fields.Monetary(string='Total Amount (Exl. Tax)', compute='_compute_total_amount', store=True, tracking=True)
    due_by = fields.Selection(selection=[('agent', 'Agent'), ('carrier', 'Carrier')], string="Due By", copy=False)
    charge_type = fields.Selection(selection=[('ppx', 'ppx (Prepaid)'), ('ccx', ' ccx (Collect)')], string="PP/CC", copy=False)

    @api.depends('measurement_basis_id')
    def _compute_is_container_type_basis(self):
        for rec in self:
            rec.is_container_type_basis = rec.measurement_basis_id and rec.measurement_basis_id == self.env.ref('freight_base.measurement_basis_container_type')

    def _modification_line_restrict_states(self):
        return []

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_address_id = False
            partner_address = self.partner_id.address_get(['invoice'])
            if partner_address.get('invoice') and partner_address.get('invoice') != self.partner_id.id:
                self.partner_address_id = partner_address.get('invoice')

    @api.onchange('container_type_id')
    def _onchange_container_type_id(self):
        for charge in self:
            if charge.is_container_type_basis and charge.container_type_id:
                shipment = charge.house_shipment_id if self._name in ['house.shipment.charge.cost', 'house.shipment.charge.revenue'] else charge.master_shipment_id
                containers = shipment.container_ids
                charge.quantity = len(containers.filtered(lambda c: c.container_type_id == charge.container_type_id))

    @api.onchange('measurement_basis_id')
    def _onchange_measurement_basis_id(self):
        charges_measure_dict = {
            self.env.ref('freight_base.measurement_basis_chargeable', raise_if_not_found=False): 'chargeable_kg',
            self.env.ref('freight_base.measurement_basis_volume', raise_if_not_found=False): 'volume_unit',
            self.env.ref('freight_base.measurement_basis_weight', raise_if_not_found=False): 'gross_weight_unit'
        }
        for charge in self.filtered(lambda c: c.measurement_basis_id):
            column = charges_measure_dict.get(charge.measurement_basis_id)
            shipment = charge.house_shipment_id if self._name in ['house.shipment.charge.cost', 'house.shipment.charge.revenue'] else charge.master_shipment_id
            master_shipment = charge.master_shipment_id if self._name in ['master.shipment.charge.cost', 'master.shipment.charge.revenue'] else None
            charge.quantity = shipment[column] if column else 1
            if charge.measurement_basis_id == self.env.ref('freight_base.measurement_basis_teu'):
                if master_shipment:
                    total_teu_count = sum(line.container_type_id.total_teu for line in master_shipment.attached_house_shipment_ids.container_ids)
                else:
                    total_teu_count = sum(line.container_type_id.total_teu for line in shipment.container_ids)
                charge.quantity = total_teu_count

            if charge.measurement_basis_id == self.env.ref('freight_base.measurement_basis_container_count'):
                if master_shipment:
                    total_container_count = len(master_shipment.attached_house_shipment_ids.container_ids)
                else:
                    total_container_count = len(shipment.container_ids)
                charge.quantity = total_container_count

            if not charge.is_container_type_basis:
                charge.container_type_id = False

    @api.constrains('measurement_basis_id', 'quantity')
    def _check_values_for_measurement_basis(self):
        measurement_basis_shipment = self.env.ref('freight_base.measurement_basis_shipment')
        measurement_container_count = self.env.ref('freight_base.measurement_basis_container_count')
        measurement_basis_teus = self.env.ref('freight_base.measurement_basis_teu')
        measurement_basis_weight = self.env.ref('freight_base.measurement_basis_weight')
        measurement_basis_volume = self.env.ref('freight_base.measurement_basis_volume')
        measurement_basis_chargeable = self.env.ref('freight_base.measurement_basis_chargeable')

        integer_measurement_basis = [measurement_basis_shipment, measurement_container_count, measurement_basis_teus]
        decimal_measurement_basis = [measurement_basis_weight, measurement_basis_volume, measurement_basis_chargeable]

        for rec in self:
            if rec.measurement_basis_id in integer_measurement_basis and (not rec.quantity.is_integer() or rec.quantity < 1):
                raise ValidationError(_('For Measurement Basis:%s - Only integer values greater than or equal to 1 allowed.') % (rec.measurement_basis_id.name))
            if rec.measurement_basis_id in decimal_measurement_basis and rec.quantity <= 0:
                raise ValidationError(_('For Measurement Basis:%s - Only Greater than 0 values should be allowed .') % (rec.measurement_basis_id.name))

    @api.depends('product_id', 'charge_description')
    def _compute_name(self):
        for rec in self:
            rec.name = f'{rec.product_id.display_name} - {rec.charge_description}'

    @api.depends('quantity', 'amount_rate')
    def _compute_total_currency_amount(self):
        for rec in self:
            rec.total_currency_amount = round(rec.amount_rate, rec.amount_currency_id.decimal_places) * rec.quantity

    def _inverse_total_currency_amount(self):
        for rec in self:
            rec.amount_rate = rec.total_currency_amount / rec.quantity

    @api.depends('amount_currency_id')
    def _compute_amount_currency_mismatch(self):
        for rec in self:
            rec.amount_currency_mismatch = rec.amount_currency_id and rec.currency_id != rec.amount_currency_id

    def _get_conversion_rate(self, currency):
        self.ensure_one()
        currency = self.env['res.currency'].sudo().with_context(company_id=self.company_id.id).search([('id', '=', currency.id)], limit=1)
        return 1/((currency and currency.rate) or 1)

    @api.onchange('amount_currency_id')
    def _onchange_amount_currency_id(self):
        for rec in self:
            rec.amount_conversion_rate = self._get_conversion_rate(rec.amount_currency_id)

    @api.depends('amount_currency_id', 'amount_rate', 'quantity', 'total_currency_amount', 'amount_conversion_rate', 'amount_currency_mismatch')
    def _compute_total_amount(self):
        for charge in self:
            conversion_rate = 1 if not charge.amount_currency_mismatch else charge.amount_conversion_rate
            charge.total_amount = round(charge.total_currency_amount * conversion_rate, 3)

    def action_update_exchange_rate(self):
        self._onchange_amount_currency_id()

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_('Please enter No of Units more than 0.'))

    def get_cost_models(self):
        return ['house.shipment.charge.cost', 'master.shipment.charge.cost']

    def get_revenue_models(self):
        return ['house.shipment.charge.revenue', 'master.shipment.charge.revenue']

    def get_shipment_models(self):
        return ['freight.house.shipment', 'freight.master.shipment']

    def get_model_field_name(self, model):
        if model in ['house.shipment.charge.revenue', 'house.shipment.charge.cost']:
            return 'house_shipment_id'
        if model in ['master.shipment.charge.revenue', 'master.shipment.charge.cost']:
            return 'master_shipment_id'

    def get_measurement_basis_domain(self, record):
        measurement_domain = []
        if record._name in self.get_shipment_models():
            if record.cargo_is_package_group:
                measurement_domain.append(('package_group', 'in', ['all', 'package']))
            else:
                measurement_domain.append(('package_group', 'in', ['all', 'container']))
        return measurement_domain

    def get_charge_domain(self, record):
        charge_domain = []
        if record._name in self.get_shipment_models():
            charge_domain = [('categ_id', '=', self.env.ref('freight_base.shipment_charge_category').id)]
        return charge_domain

    def skip_debtor_model(self):
        return ['master.shipment.charge.revenue']

    @api.model
    def action_charges_download(self, shipment_id):
        shipment = self.env[model_dict[self._name]].browse(int(shipment_id))
        return self.action_excel_download_charges_template(shipment)

    @api.model
    def action_charges_upload(self, shipment_id):
        shipment_id = self.env[model_dict[self._name]].browse(int(shipment_id))
        return self.action_open_wizard_upload_charges(shipment_id)

    def excel_write_charge_lines(self, workbook, worksheet):
        return workbook, worksheet

    def action_excel_download_charges_template(self, shipment_id):
        # Create an in-memory Excel file
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = self.excel_get_worksheet_with_header(workbook, shipment_id)

        # Write the data
        self.excel_write_shipment_charge_lines(workbook, worksheet, shipment_id)

        # Close the workbook
        workbook.close()

        # Return the Excel file as an attachment
        rec_type = 'Cost' if self._name in self.get_cost_models() else 'Revenue'
        filename = '%s-%s.xlsx' % (rec_type, shipment_id.name)

        content = output.getvalue()
        AttachmentObj = self.env['ir.attachment']
        attachment = AttachmentObj.search([('name', '=', filename)], limit=1)
        if not attachment:
            attachment = AttachmentObj.create({
                'name': filename,
                'datas': base64.b64encode(content),
                'store_fname': filename,
                'res_model': self._name,
                'res_id': 0,
                'type': 'binary',
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })
        else:
            attachment.write({'datas': base64.b64encode(content)})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true&filename=%s' % (attachment.id, filename),
            'target': 'new',
        }

    def excel_get_worksheet_with_header(self, workbook, shipment):
        worksheet = workbook.add_worksheet()
        heading_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '11px', 'valign': 'vcenter'})

        # Write the headers with locked formatting
        headers = [_('Sr. No.'), _('Charge Name'), _('Charge Description'), _('No Of Units'), _('Measurement Basis'), _('Debtor'), _('Currency'),  _('Rate Per Unit')]
        unit_rate_column = 'H'
        if self._name in self.get_cost_models():
            headers.remove(_('Debtor'))
            headers.insert(5, _('Creditor'))
        if self._name in self.skip_debtor_model():
            headers.remove(_('Debtor'))
            unit_rate_column = 'G'

        header_row = 0
        for col, header in enumerate(headers):
            worksheet.write(header_row, col, header, heading_style)

        # Set column width
        [worksheet.set_column(1, col, 20) for col in range(4, 10)]

        # Add ID at cell number 100 - CW
        worksheet.write(header_row, 100, 'ID', heading_style)

        # Hide ID Column
        worksheet.set_column('CW:CW', None, None, {'hidden': 1})

        # Data validation Rule: to allow only Decimal value greater-than/equal to zero
        number_rule = {
            'validate': 'decimal',
            'criteria': '>=',
            'value': 0,
            'error_message': _('Only numeric values are allowed')
        }
        worksheet.data_validation('D2:D200', number_rule)
        worksheet.data_validation('{}2:{}200'.format(unit_rate_column, unit_rate_column), number_rule)

        # Data validation Rule: to allow only defined measurement basis
        measurement_domain = self.get_measurement_basis_domain(shipment)
        measurement_basis = self.env['freight.measurement.basis'].search(measurement_domain)
        measurement_value_rule = {
            'validate': 'list',
            'source': [mb.name for mb in measurement_basis],
            'input_title': _('Measurement Basis'),
            'input_message': _('Select a measurement value from the list'),
        }
        worksheet.data_validation('E2:E200', measurement_value_rule)

        # Data validation Rule: to allow only defined charges
        charge_domain = self.get_charge_domain(shipment)
        charge_type = self.env['product.product'].search(charge_domain)
        charge_type_value_rule = {
            'validate': 'list',
            'source': [ct.name for ct in charge_type],
            'input_title': _('Charge Name'),
            'input_message': _('Select a charge-name from the list'),
        }
        worksheet.data_validation('B2:B200', charge_type_value_rule)

        return worksheet

    def excel_write_shipment_charge_lines(self, workbook, worksheet, shipment_id):
        cell_right = workbook.add_format({'align': 'right', 'valign': 'vcenter'})
        cell_left = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
        record_ids = shipment_id.revenue_charge_ids if self._name in self.get_revenue_models() else shipment_id.cost_charge_ids
        for row, charge in enumerate(record_ids):
            worksheet.write(row + 1, 0, row + 1, cell_right)
            worksheet.write(row + 1, 1, charge.sudo().product_id.name, cell_left)
            worksheet.write(row + 1, 2, charge.charge_description or '', cell_left)
            worksheet.write(row + 1, 3, charge.quantity, cell_right)
            worksheet.write(row + 1, 4, charge.measurement_basis_id.name, cell_left)
            column = 4
            if self._name not in self.skip_debtor_model():
                worksheet.write(row + 1, column + 1, charge.partner_id.name or '', cell_left)
                column = 5
            worksheet.write(row + 1, column + 1, charge.amount_currency_id.name, cell_left)
            worksheet.write(row + 1, column + 2, charge.amount_rate, cell_right)
            worksheet.write(row + 1, 100, charge.id, cell_right)

    def action_open_wizard_upload_charges(self, shipment_id):
        return {
            'name': _('Upload Charges'),
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.upload.charges',
            'views': [[False, 'form']],
            'context': {
                'default_shipment_model': shipment_id._name,
                'default_shipment_rec': shipment_id.id,
                'default_model_name': self._name,
                },
            'target': 'new'
        }

    def update_create_charge_line(self, shipment_id, model, charge_id, vals):
        field_name = self.get_model_field_name(model)
        vals.update({field_name: shipment_id.id})
        if charge_id:
            charge_id.write(vals)
        else:
            charge_id = self.env[model].create(vals)
            charge_id._onchange_amount_currency_id()

        return

    def action_option_from_view(self):
        self.ensure_one()
        shipment_status = self.house_shipment_id.state if self._name in ['house.shipment.charge.cost', 'house.shipment.charge.revenue'] else self.master_shipment_id.state
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'context': {'from_copy_method': True, **self._context,
                        'edit': shipment_status not in ['cancelled'] if not self.env.user.has_group('freight_management.group_super_admin') else True,
                        },
        }

    def check_charges_rate_per_unit(self, name):
        if any(charge.amount_rate <= 0 for charge in self):
            raise ValidationError(_("You can't create %s with 0 amount.") % (name))
