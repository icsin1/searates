import json
import logging
import datetime
import base64
import io
import xlsxwriter
import xlrd
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class TariffMixin(models.AbstractModel):
    _name = 'tariff.mixin'
    _description = 'Tariff Mixin Properties'
    _rec_name = 'tariff_name'
    _order = 'create_date DESC'

    @api.depends('transport_mode_id')
    def _compute_cargo_type_domain(self):
        for rec in self:
            domain = [('transport_mode_id', '=', rec.transport_mode_id.id)]
            rec.cargo_type_domain = json.dumps(domain)

    @api.depends('destination_id', 'destination_id.country_id')
    def _compute_destination_country(self):
        for rec in self:
            if rec.destination_id:
                rec.destination_country_id = rec.destination_id.country_id
            else:
                rec.destination_country_id = rec.destination_country_id

    @api.depends('origin_id', 'origin_id.country_id')
    def _compute_origin_country(self):
        for rec in self:
            if rec.origin_id:
                rec.origin_country_id = rec.origin_id.country_id
            else:
                rec.origin_country_id = rec.origin_country_id

    cargo_type_domain = fields.Char(compute='_compute_cargo_type_domain', store=True)

    tariff_name = fields.Char(required=True, string='Tariff Name', default='New Tariff')
    tariff_for = fields.Selection([
        ('shipment', 'Shipment'),
    ], default='shipment', string="Type")
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id)
    shipment_type_id = fields.Many2one('shipment.type')
    transport_mode_id = fields.Many2one('transport.mode')
    transport_mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True, string='Transport Mode Type')
    cargo_type_id = fields.Many2one('cargo.type')
    origin_id = fields.Many2one('freight.un.location', string='Origin', copy=False)
    origin_country_id = fields.Many2one('res.country', compute='_compute_origin_country', store=True, string='Origin Country')
    origin_port_id = fields.Many2one('freight.port', domain="[('country_id', '=', origin_country_id), ('transport_mode_id', '=', transport_mode_id)]")
    destination_id = fields.Many2one('freight.un.location', string='Destination', copy=False)
    destination_country_id = fields.Many2one('res.country', compute='_compute_destination_country', store=True, string='Destination Country')
    destination_port_id = fields.Many2one('freight.port', domain="[('country_id', '=', destination_country_id), ('transport_mode_id', '=', transport_mode_id)]")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    active = fields.Boolean(default=True)
    import_error_message = fields.Html()
    domain_measurement_ids = fields.Many2many('freight.measurement.basis', string='Domain Measurement Basis', compute='_compute_domain_measurement_basis', store=True)
    carrier_id = fields.Many2one('freight.carrier', string="Carrier", domain="[('transport_mode_id', '=', transport_mode_id)]")
    mode_type = fields.Selection(related='transport_mode_id.mode_type', store=True, string='Mode Type')

    @api.depends('cargo_type_id')
    def _compute_domain_measurement_basis(self):
        for rec in self:
            if rec.cargo_type_id.is_package_group:
                domain = [('package_group', 'in', ['all', 'package'])]
            else:
                domain = [('package_group', 'in', ['all', 'container'])]
            rec.domain_measurement_ids = self.env['freight.measurement.basis'].search(domain).ids

    @api.onchange('origin_country_id')
    def _onchange_origin_country_id(self):
        if self.origin_id and self.origin_country_id != self.origin_id.country_id:
            self.origin_id = False

    @api.onchange('destination_country_id')
    def _onchange_destination_country_id(self):
        if self.destination_id and self.destination_country_id != self.destination_id.country_id:
            self.destination_id = False

    @api.onchange('origin_id')
    def _onchange_origin_id(self):
        if self.origin_country_id != self.origin_port_id.country_id:
            self.origin_port_id = False

    @api.onchange('destination_id')
    def _onchange_destination_id(self):
        if self.destination_country_id != self.destination_port_id.country_id:
            self.destination_port_id = False

    @api.onchange('transport_mode_id')
    def _onchange_transport_mode_id(self):
        values = {'cargo_type_id': False, 'carrier_id': False}
        self.update(values)

    def excel_write_charge_lines(self, workbook, worksheet):
        return workbook, worksheet

    def action_excel_download_charges_template(self):
        self.ensure_one()

        self.import_error_message = False
        # Create an in-memory Excel file
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        worksheet = self.excel_get_worksheet_with_header(workbook)

        # Write the data
        self.excel_write_charge_lines(workbook, worksheet)

        # Close the workbook
        workbook.close()

        # Return the Excel file as an attachment
        filename = '%s_Charges.xlsx' % (self.tariff_name.replace('.', ''))
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

    def excel_get_worksheet_with_header(self, workbook):
        worksheet = workbook.add_worksheet()
        heading_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '11px', 'valign': 'vcenter'})

        # Write the headers with locked formatting
        headers = ['Sr. No.', 'Charge Name', 'Unit Price', 'Currency', 'Measurement Basis', 'Valid From(YYYY/MM/DD)', 'Valid To(YYYY/MM/DD)']
        header_row = 0
        for col, header in enumerate(headers):
            worksheet.write(header_row, col, header, heading_style)

        # Set column width
        [worksheet.set_column(1, col, 20) for col in range(4, 7)]

        # Data validation Rule: to allow only Decimal value greater-than/equal to zero
        number_rule = {
            'validate': 'decimal',
            'criteria': '>=',
            'value': 0,
            'error_message': 'Only numeric values are allowed'
        }
        worksheet.data_validation('C2:C200', number_rule)

        # Data validation Rule: to allow only defined measurement basis
        measurement_basis = self.env['freight.measurement.basis'].search([])
        measurement_value_rule = {
            'validate': 'list',
            'source': [mb.name for mb in measurement_basis],
            'input_title': 'Measurement Basis',
            'input_message': _('Select a measurement value from the list'),
        }
        worksheet.data_validation('E2:E200', measurement_value_rule)

        # Data validation Rule: to allow only defined charges
        charge_type = self.env['product.product'].search([('categ_id', '=', self.env.ref('freight_base.shipment_charge_category').id)])
        charge_type_value_rule = {
            'validate': 'list',
            'source': [ct.name for ct in charge_type],
            'input_title': 'Charge Name',
            'input_message': _('Select a charge-name from the list'),
        }
        worksheet.data_validation('B2:B200', charge_type_value_rule)

        # Data Validation Rule: Date format
        number_rule = {
            'validate': 'date',
            'criteria': '>',
            'value': datetime.datetime.strptime('0600/01/30', "%Y/%m/%d"),
            'error_message': _('Only valid-date allowed in YYYY/MM/DD format')
        }
        worksheet.data_validation('F2:G200', number_rule)
        return worksheet

    def update_create_tariff_line(self, charge_type, unit_price, currency, measurement, valid_from, valid_to):
        pass

    def excel_process_data(self, workbook):
        self.ensure_one()
        row_processing_message = {}
        worksheet = workbook.sheet_by_index(0)

        if worksheet.ncols < 7:
            self.import_error_message = 'Enough column data not found from file. You can Download and refer Template file!'
            return False

        ProductObj = self.env['product.product']
        CurrencyObj = self.env['res.currency']
        MeasurementBasisObj = self.env['freight.measurement.basis']

        def is_digit(string):
            try:
                return float(string)
            except Exception:
                return 0

        for rowx, row in enumerate(map(worksheet.row, range(1, worksheet.nrows)), 1):
            row_skipped = []
            charge_name = row[1].value
            unit_price = row[2].value
            currency_name = row[3].value
            measurement_basis = row[4].value

            valid_from = row[5].value or ''
            valid_to = row[6].value or ''

            # Skip only column-data import, not the row in case error found in Optional-value
            try:
                if isinstance(valid_from, str):
                    valid_from = datetime.datetime.strptime(valid_from, "%Y/%m/%d")
                else:
                    valid_from = xlrd.xldate.xldate_as_datetime(valid_from, workbook.datemode)
            except Exception:
                valid_from = False
            try:
                if isinstance(valid_to, str):
                    valid_to = datetime.datetime.strptime(valid_to, "%Y/%m/%d")
                else:
                    valid_to = xlrd.xldate.xldate_as_datetime(valid_to, workbook.datemode)
            except Exception:
                valid_to = False

            charge_type = ProductObj.search([('name', '=', charge_name)], limit=1)
            if not charge_type:
                row_skipped.append('Charge name {} not found.'.format(charge_name))

            if not is_digit(unit_price):
                row_skipped.append('Wrong value {} for Charge Price.'.format(unit_price))
            else:
                unit_price = is_digit(unit_price)

            currency = CurrencyObj.search([('name', '=', currency_name)], limit=1)
            if not currency:
                row_skipped.append('Currency name {} not found.'.format(currency_name))

            measurement = MeasurementBasisObj.search([('name', '=', measurement_basis)])
            if not measurement:
                row_skipped.append('Measurement Basis {} not found.'.format(measurement_basis))

            if row_skipped:
                row_processing_message[rowx + 1] = row_skipped
            else:
                self.update_create_tariff_line(charge_type, unit_price, currency, measurement, valid_from, valid_to)
        if row_processing_message:
            self.import_error_message = '<br/>'.join(['''Skipped Row-{}: {}'''.format(row_num, ','.join(row_processing_message[row_num])) for row_num in row_processing_message])
            return False
        return True

    def action_excel_upload_charges(self, **kwargs):
        self.ensure_one()

        attachment = self.env['ir.attachment'].sudo().browse(kwargs.get('attachment_ids', []))
        if not attachment:
            self.import_error_message = 'File not uploaded properly. Please check file and upload file again!'
            return True

        try:
            workbook = xlrd.open_workbook(file_contents=base64.b64decode(attachment.datas) or b'')
        except Exception as e:
            _logger.warning(e)
            workbook = False
            self.import_error_message = 'Could not read file properly, Please check file extension(Excel file) or file-data and upload file again!'
            return True

        try:
            # Process Data
            process_succeed = self.excel_process_data(workbook)
        except Exception as e:
            _logger.warning(e)
            self.import_error_message = 'Could not process file properly, Please verify file contains data as per Template file, and upload file again!'
            return True
        if process_succeed:
            self.import_error_message = False
        return True

    def download_error_message_file(self):
        self.ensure_one()
        data = io.StringIO()
        data.write('<h2>Error in Upload-Process:{}</h2>{}'.format(self.tariff_name, self.import_error_message))
        content = data.getvalue().encode("utf-8")
        data.close()
        filename = 'Errors_%s.html' % (self.tariff_name.replace('.', ''))
        AttachmentObj = self.env['ir.attachment']
        attachment = AttachmentObj.search([('name', '=', filename)], limit=1)
        if not attachment:
            attachment = AttachmentObj.create({
                'name': filename, 'datas': base64.b64encode(content), 'store_fname': filename, 'res_model': self._name, 'type': 'binary', 'mimetype': 'text/html'})
        else:
            attachment.write({'datas': base64.b64encode(content)})
        ret = {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true&filename=%s' % (attachment.id, filename),
            'target': 'new',
        }
        return ret


class TariffMixinLine(models.AbstractModel):
    _name = 'tariff.mixin.line'
    _description = 'Tariff Mixin Line Properties'
    _order = 'date_to DESC'

    def get_charge_domain(self):
        self.ensure_one()
        charge_category = self.env.ref('freight_base.shipment_charge_category', raise_if_not_found=False)
        return json.dumps(['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False), ('categ_id', '=', charge_category.id)])

    @api.depends('company_id')
    def _compute_charge_domain(self):
        for service in self:
            service.charge_domain = service.get_charge_domain()

    charge_domain = fields.Char(compute='_compute_charge_domain')
    charge_type_id = fields.Many2one('product.product', required=True, string="Charge Name")
    charge_type_uom_id = fields.Many2one('uom.uom', related='charge_type_id.uom_id', store=True)
    unit_price = fields.Monetary('Unit Price', required=True, default=None)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=lambda self: self.env.company.currency_id)
    measurement_basis_id = fields.Many2one('freight.measurement.basis', required=True, default=lambda self: self.env.ref('freight_base.measurement_basis_shipment', raise_if_not_found=False))
    date_from = fields.Date(string='Valid From')
    date_to = fields.Date(string='Valid To')
    is_active_charge = fields.Boolean(compute='_compute_is_active_charge', store=True)

    # Container Type based Measurement Basis
    is_container_type_basis = fields.Boolean(compute='_compute_is_container_type_basis')
    container_type_id = fields.Many2one('freight.container.type', string='Container Type')

    @api.depends('measurement_basis_id')
    def _compute_is_container_type_basis(self):
        """
        Compute method to determine if the Measurement basis is 'Container type'.
        If the Measurement basis is 'Container type',  is_container_type_basis will be True OR False
        """
        for rec in self:
            rec.is_container_type_basis = rec.measurement_basis_id and rec.measurement_basis_id == self.env.ref('freight_base.measurement_basis_container_type')

    @api.onchange('charge_type_id')
    def _onchange_charge_type(self):
        if self.charge_type_id:
            self.measurement_basis_id = self.charge_type_id.measurement_basis_id.id

    @api.depends('date_from', 'date_to')
    def _compute_is_active_charge(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_active_charge = (not rec.date_from and not rec.date_to) or (
                (not rec.date_from or rec.date_from <= today) and (not rec.date_to or rec.date_to >= today)
            )
