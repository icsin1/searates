import base64
import xlrd
import logging

from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WizardUploadCharges(models.TransientModel):
    _name = 'wizard.upload.charges'
    _description = 'Upload Charges'

    shipment_model = fields.Char(string='Shipment Model')
    shipment_rec = fields.Integer(string='Shipment Record')
    import_file = fields.Binary(string='Import Excel File')
    import_filename = fields.Char()
    model_name = fields.Char(string='Model')
    import_error_message = fields.Html('Error Message')

    def action_process_file(self):
        self.ensure_one()
        if not self.import_file:
            raise UserError("File Not found.")

        try:
            workbook = xlrd.open_workbook(file_contents=base64.b64decode(self.import_file))
        except Exception as e:
            _logger.warning(e)
            workbook = False
            self.import_error_message = 'Could not read file properly, Please check file extension(Excel file) or file-data and upload file again!'
            return self.open_upload_wizard()

        try:
            # Process Data
            process_succeed = self.excel_process_charges_data(workbook)
        except Exception as e:
            _logger.warning(e)
            self.import_error_message = 'Could not process file properly, Please verify file contains data as per Template file, and upload file again!'
            return self.open_upload_wizard()

        if process_succeed:
            self.import_error_message = False
        else:
            return self.open_upload_wizard()
        return

    def excel_process_charges_data(self, workbook):
        self.ensure_one()
        row_processing_message = {}
        worksheet = workbook.sheet_by_index(0)

        MixinObj = self.env['mixin.freight.charge']
        column_count = 8
        if self.model_name in MixinObj.skip_debtor_model():
            column_count = 7
        if worksheet.ncols < column_count:
            self.import_error_message = 'Enough column data not found from file. You can Download and refer Template file!'
            return False

        ProductObj = self.env['product.product']
        CurrencyObj = self.env['res.currency']
        PartnerObj = self.env['res.partner']
        MeasurementBasisObj = self.env['freight.measurement.basis']

        def is_digit(string):
            try:
                return float(string)
            except Exception:
                return 0

        shipment = self.env[self.shipment_model].browse(self.shipment_rec)
        for rowx, row in enumerate(map(worksheet.row, range(1, worksheet.nrows)), 1):
            row_skipped = []
            charge_id = row[100].value and self.env[self.model_name].browse(int(row[100].value)).exists() or False

            charge_name = row[1].value
            charge_desc = row[2].value
            quantity = row[3].value
            measurement_basis_name = row[4].value
            column = 4
            partner_name = ''
            if self.model_name not in MixinObj.skip_debtor_model():
                partner_name = row[column + 1].value
                column = 5
            currency_name = row[column + 1].value
            unit_price = row[column + 2].value

            # Skip only column-data import, not the row in case error found in Optional-value
            product_id = ProductObj.search([('name', '=', charge_name)], limit=1)
            if not product_id:
                row_skipped.append('Charge name {} not found.'.format(charge_name))

            if not is_digit(quantity):
                row_skipped.append('Wrong value {} for No of Units.'.format(quantity))
            else:
                quantity = is_digit(quantity)

            if not is_digit(unit_price):
                row_skipped.append('Wrong value {} for Charge Price.'.format(unit_price))
            else:
                unit_price = is_digit(unit_price)

            partner_id = PartnerObj.search([('name', '=', partner_name)], limit=1)
            if not partner_id and self.model_name not in MixinObj.skip_debtor_model():
                partner_type = 'Debtor' if self.model_name in MixinObj.get_revenue_models() else 'Creditor'
                row_skipped.append('{} name {} not found.'.format(partner_type, partner_name))

            currency_id = CurrencyObj.search([('name', '=', currency_name)], limit=1)
            if not currency_id:
                row_skipped.append('Currency name {} not found.'.format(currency_name))

            measurement_id = MeasurementBasisObj.search([('name', '=', measurement_basis_name)])
            if not measurement_id:
                row_skipped.append('Measurement Basis {} not found.'.format(measurement_basis_name))
            else:
                MeasurementBasisObj = self.env['freight.measurement.basis']
                allowed_measurement_basis = MeasurementBasisObj.search(MixinObj.get_measurement_basis_domain(shipment))

                if measurement_id not in allowed_measurement_basis:
                    row_skipped.append('%s not allowed. Only %s measurement basis allowed.' % (measurement_basis_name, ','.join(allowed_measurement_basis.mapped('name'))))

            if charge_id and charge_id.status not in ['no', 'partial']:
                row_skipped.append("{}: You can't modify '{}' charges.".format(charge_id.name, str(charge_id.status).replace('_', ' ').title()))

            if row_skipped:
                row_processing_message[rowx + 1] = row_skipped
            else:
                vals = {
                        'product_id': product_id.id,
                        'charge_description': charge_desc,
                        'quantity': quantity,
                        'measurement_basis_id': measurement_id.id,
                        'partner_id': partner_id.id,
                        'amount_currency_id': currency_id.id,
                        'amount_rate': unit_price
                    }
                MixinObj.update_create_charge_line(shipment, self.model_name, charge_id, vals)

        if row_processing_message:
            self.import_error_message = '<br/>'.join(['''Skipped Row-{}: {}'''.format(row_num, ','.join(row_processing_message[row_num])) for row_num in row_processing_message])
            return False

        return True

    def open_upload_wizard(self):
        self.ensure_one()
        return {
            'name': _('Upload Charges'),
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.upload.charges',
            'views': [[False, 'form']],
            'res_id': self.id,
            'target': 'new',
            'context': {'hide_process_button': True},
        }
