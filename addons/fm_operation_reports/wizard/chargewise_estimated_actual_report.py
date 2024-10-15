# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import base64
import io
import xlsxwriter
from itertools import groupby
from odoo.exceptions import ValidationError


class ChargewiseEstimatedActualReport(models.TransientModel):
    _name = 'chargewise.estimated.actual.report'
    _description = 'Chargewise Estimated Actual Report'

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    transport_mode_id = fields.Many2one('transport.mode', string='Transport Mode')
    shipment_type_id = fields.Many2one('shipment.type', string='Shipment Type')
    cargo_type_id = fields.Many2one('cargo.type', domain="[('transport_mode_id', '=', transport_mode_id)]", string="Cargo Type")
    service_job = fields.Boolean(string='Service Job')

    @api.constrains('from_date', 'to_date')
    def _check_from_date_to_date(self):
        for rec in self:
            if rec.to_date < rec.from_date:
                raise ValidationError(_('"To date" must be greater than or equal to the "from date"'))

    def generate_report_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        header_style = workbook.add_format({'align': 'center', 'bold': True})
        line_style = workbook.add_format({'align': 'center'})
        worksheet = workbook.add_worksheet('Charge Wise Shipment Estimated VS Actual')
        worksheet.set_column(0, 18, 20)

        worksheet.write(0, 0, 'Company', header_style)
        worksheet.write(0, 1, 'Transport Mode', header_style)
        worksheet.write(0, 2, 'Shipment Type', header_style)
        worksheet.write(0, 3, 'Cargo Type', header_style)
        worksheet.write(0, 4, 'Shipment Number - Booking Ref / Nomination No ', header_style)
        worksheet.write(0, 5, 'Shipment Date', header_style)
        worksheet.write(0, 6, 'Shipment / Service Job', header_style)
        worksheet.write(0, 7, 'Sales Agent', header_style)
        worksheet.write(0, 8, 'Customer Name', header_style)
        worksheet.write(0, 9, 'Shipper Name', header_style)
        worksheet.write(0, 10, 'Consignee Name', header_style)
        worksheet.write(0, 11, 'Charge Code', header_style)
        worksheet.write(0, 12, 'Charge Name', header_style)
        worksheet.write(0, 13, 'Estimated Revenue', header_style)
        worksheet.write(0, 14, 'Estimated Revenue Currency', header_style)
        worksheet.write(0, 15, 'Estimated Revenue Exch. Rate', header_style)
        worksheet.write(0, 16, 'Estimated Revenue in Company Currency', header_style)
        worksheet.write(0, 17, 'Estimated Cost', header_style)
        worksheet.write(0, 18, 'Estimated cost Currency', header_style)
        worksheet.write(0, 19, 'Estimated Cost Exch. Rate.', header_style)
        worksheet.write(0, 20, 'Estimated Cost in Company Currency', header_style)
        worksheet.write(0, 21, 'Estimated Profit', header_style)
        worksheet.write(0, 22, 'Actual Revenue', header_style)
        worksheet.write(0, 23, 'Actual Revenue Currency', header_style)
        worksheet.write(0, 24, 'Actual Revenue Exch. Rate.', header_style)
        worksheet.write(0, 25, 'Actual Revenue in Company Currency', header_style)
        worksheet.write(0, 26, 'Actual Cost', header_style)
        worksheet.write(0, 27, 'Actual cost Currency', header_style)
        worksheet.write(0, 28, 'Actual Cost Exch. Rate.', header_style)
        worksheet.write(0, 29, 'Actual Cost in Company Currency ', header_style)
        worksheet.write(0, 30, 'Actual Profit', header_style)

        domain = [('shipment_date', '>=', self.from_date),
                  ('shipment_date', '<=', self.to_date)]
        if self.transport_mode_id:
            domain.append(('transport_mode_id', '=', self.transport_mode_id.id))
        if self.cargo_type_id:
            domain.append(('cargo_type_id', '=', self.cargo_type_id.id))
        if self.shipment_type_id:
            domain.append(('shipment_type_id', '=', self.shipment_type_id.id))

        shipments = self.env['freight.house.shipment'].search(domain)
        shipments_list = []
        service_jobs_list = []
        for shipment in shipments:
            company_id = shipment.company_id and shipment.company_id.name or ''
            transport_mode = shipment.transport_mode_id and shipment.transport_mode_id.name or ''
            shipment_type = shipment.shipment_type_id and shipment.shipment_type_id.name or ''
            cargo_type = shipment.cargo_type_id and shipment.cargo_type_id.name or ''
            booking_nomination_no = shipment.booking_nomination_no or ''
            shipment_date = shipment.shipment_date and shipment.shipment_date.strftime('%m/%d/%Y') or ''
            shipment_service_job = 'Shipment'
            sales_agent = shipment.sales_agent_id and shipment.sales_agent_id.name or ''
            customer = shipment.client_id and shipment.client_id.name or ''
            shipper = shipment.shipper_id and shipment.shipper_id.name or ''
            consignee = shipment.consignee_id and shipment.consignee_id.name or ''

            total_actual_revenue = []
            actual_revenue_dict = {}
            actual_cost_dict = {}
            actual_profit_dict = {}
            for jobsheet in shipment.job_costsheet_ids:
                if jobsheet.product_id not in total_actual_revenue:
                    total_actual_revenue.append(jobsheet.product_id)
                if jobsheet.product_id.display_name in actual_revenue_dict.keys():
                    actual_revenue_dict[jobsheet.product_id.display_name]['amount'] += jobsheet.revenue_actual_total_amount
                else:
                    actual_revenue_dict.update({jobsheet.product_id.display_name: {
                        'amount': jobsheet.revenue_actual_total_amount,
                        'currency_id': jobsheet.currency_id}})
                if jobsheet.product_id.display_name in actual_cost_dict.keys():
                    actual_cost_dict[jobsheet.product_id.display_name]['amount'] += jobsheet.cost_actual_total_amount
                else:
                    actual_cost_dict.update({jobsheet.product_id.display_name: {
                        'amount': jobsheet.cost_actual_total_amount,
                        'currency_id': jobsheet.currency_id}})
                if jobsheet.product_id.display_name in actual_profit_dict.keys():
                    actual_profit_dict[jobsheet.product_id.display_name]['amount'] += jobsheet.actual_margin
                else:
                    actual_profit_dict.update({jobsheet.product_id.display_name: {'amount': jobsheet.actual_margin,
                                                                                  'currency_id': jobsheet.currency_id
                                                                                  }})
            total_charges = [{}]
            charges_dict = {}
            for revenue_charge in shipment.revenue_charge_ids:
                if revenue_charge.product_id not in total_charges[0].keys():
                    total_charges[0].update(
                        {revenue_charge.product_id: {'currency_id': revenue_charge.amount_currency_id,
                                                     'exchange_rate': revenue_charge.amount_conversion_rate
                                                     }})
                else:
                    if revenue_charge.amount_currency_id != total_charges[0].get(revenue_charge.product_id).get('currency_id'):
                        total_charges[0].update(
                            {revenue_charge.product_id: {'currency_id': revenue_charge.amount_currency_id,
                                                         'exchange_rate': revenue_charge.amount_conversion_rate
                                                         }})

                if revenue_charge.product_id.display_name in charges_dict.keys():
                    if (revenue_charge.amount_currency_id in
                            charges_dict[revenue_charge.product_id.display_name].keys()):
                        charges_dict[revenue_charge.product_id.display_name][revenue_charge.amount_currency_id]['amount'] \
                            += revenue_charge.total_currency_amount
                    else:
                        charges_dict[revenue_charge.product_id.display_name].update({
                            revenue_charge.amount_currency_id: {'amount': revenue_charge.total_currency_amount,
                                                                'exchange_rate': revenue_charge.amount_conversion_rate}})
                else:
                    charges_dict.update({revenue_charge.product_id.display_name: {
                        revenue_charge.amount_currency_id: {'amount': revenue_charge.total_currency_amount,
                                                            'exchange_rate': revenue_charge.amount_conversion_rate}}})
            cost_dict = {}
            for revenue_cost in shipment.cost_charge_ids:
                if revenue_cost.product_id not in total_charges[0].keys():
                    total_charges[0].update(
                        {revenue_cost.product_id: {'currency_id': revenue_cost.amount_currency_id,
                                                   'exchange_rate': revenue_cost.amount_conversion_rate
                                                   }})
                else:
                    if revenue_cost.amount_currency_id != total_charges[0].get(revenue_cost.product_id).get('currency_id'):
                        total_charges[0].update(
                            {revenue_cost.product_id: {'currency_id': revenue_cost.amount_currency_id,
                                                       'exchange_rate': revenue_cost.amount_conversion_rate
                                                       }})
                if revenue_cost.product_id.display_name in cost_dict.keys():
                    if (revenue_cost.amount_currency_id in
                            cost_dict[revenue_cost.product_id.display_name].keys()):
                        cost_dict[revenue_cost.product_id.display_name][revenue_cost.amount_currency_id]['amount'] \
                            += revenue_cost.total_currency_amount
                    else:
                        cost_dict[revenue_cost.product_id.display_name].update({
                            revenue_cost.amount_currency_id: {'amount': revenue_cost.total_currency_amount,
                                                              'exchange_rate': revenue_cost.amount_conversion_rate}})
                else:
                    cost_dict.update({revenue_cost.product_id.display_name: {
                        revenue_cost.amount_currency_id: {'amount': revenue_cost.total_currency_amount,
                                                          'exchange_rate': revenue_cost.amount_conversion_rate}}})
            # for charge in total_charges[0]:
            final_dict = {}
            for key, value in charges_dict.items():
                final_dict[key] = {}
                for key, value in charges_dict.items():
                    final_dict[key] = {}
                    for currency, charge in value.items():
                        cost_data = cost_dict.get(key, {}).get(currency)
                        cost_amount = cost_data['amount'] if cost_data and 'amount' in cost_data else 0
                        final_dict[key][currency] = {'charge': charge['amount'], 'cost': cost_amount,
                                                     'exchange_rate': charge['exchange_rate']}
                for key, value in cost_dict.items():
                    if key not in final_dict:
                        final_dict[key] = {}
                    for currency, cost in value.items():
                        if currency not in final_dict.get(key, {}):
                            final_dict[key][currency] = {'charge': 0, 'cost': cost['amount'],
                                                         'exchange_rate': cost['exchange_rate']}
            for product_charge in final_dict:
                for currency_vise_charge in final_dict[product_charge]:
                    charge_code = product_charge or ''
                    charge_string = product_charge.split(' ')
                    charge_name = ' '.join(charge_string[1:]) if '[' in charge_string[0] else ' '.join(charge_string) or ''
                    estimated_revenue_cost_currency = currency_vise_charge.symbol
                    estimated_revenue = final_dict[product_charge][currency_vise_charge].get('charge')# charges_dict.get(charge.display_name) or 0.0
                    estimated_cost = final_dict[product_charge][currency_vise_charge].get('cost')# cost_dict.get(charge.display_name) or 0.0
                    # estimated_profit = estimated_revenue - estimated_cost
                    estimated_profit = (estimated_revenue * final_dict[product_charge][currency_vise_charge]
                                        .get('exchange_rate')) - (estimated_cost *
                                                                  final_dict[product_charge][currency_vise_charge]
                                                                  .get('exchange_rate'))

                    actual_revenue = actual_revenue_dict.get(product_charge)['amount'] or 0.0
                    actual_revenue_currency = actual_revenue_dict.get(product_charge)['currency_id'].symbol
                    actual_cost = actual_cost_dict.get(product_charge)['amount'] or 0.0
                    actual_cost_currency = actual_cost_dict.get(product_charge)['currency_id'].symbol
                    actual_profit = actual_profit_dict.get(product_charge)['amount'] or 0.0
                    shipments_list.append({
                        'company_id': company_id,
                        'transport_mode': transport_mode,
                        'shipment_type': shipment_type,
                        'cargo_type': cargo_type,
                        'booking_nomination_no': booking_nomination_no,
                        'date': shipment_date,
                        'shipment_service_job': shipment_service_job,
                        'sales_agent': sales_agent,
                        'customer': customer,
                        'shipper': shipper,
                        'consignee': consignee,
                        'charge_code': charge_code,
                        'charge_name': charge_name,
                        'estimated_revenue': estimated_revenue,
                        'estimated_revenue_cost_currency': estimated_revenue_cost_currency,
                        'estimated_revenue_in_company_currency': estimated_revenue *
                                                                 final_dict[product_charge][currency_vise_charge].get('exchange_rate'),
                        'estimated_cost': estimated_cost,
                        'estimated_cost_in_company_currency': estimated_cost * final_dict[product_charge][currency_vise_charge].get('exchange_rate'),
                        'estimated_profit': estimated_profit,
                        'actual_revenue': actual_revenue,
                        'actual_revenue_currency': actual_revenue_currency,
                        'actual_revenue_exchange_rate': 1,
                        'actual_revenue_in_company_currency': 1 * actual_revenue,
                        'actual_cost': actual_cost,
                        'actual_cost_currency': actual_cost_currency,
                        'actual_cost_exchange_rate': 1,
                        'actual_cost_in_company_currency': 1 * actual_cost,
                        'actual_profit': 1 * actual_profit,
                        'exchange_rate': final_dict[product_charge][currency_vise_charge].get('exchange_rate')
                    })

        if self.service_job:
            serive_job_domain = [('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]
            service_jobs = self.env['freight.service.job'].search(serive_job_domain)
            for service_job in service_jobs:
                company_id = service_job.company_id and service_job.company_id.name or ''
                transport_mode = service_job.transport_mode_id and service_job.transport_mode_id.name or ''
                shipment_type = service_job.shipment_type_id and service_job.shipment_type_id.name or ''
                cargo_type = service_job.cargo_type_id and service_job.cargo_type_id.name or ''
                booking_nomination_no = service_job.booking_nomination_no or ''
                date = service_job.date and service_job.date.strftime('%m/%d/%Y') or ''
                shipment_service_job = 'Service Job'
                sales_agent = service_job.sales_agent_id and service_job.sales_agent_id.name or ''
                customer = service_job.client_id and service_job.client_id.name or ''
                shipper = service_job.shipper_id and service_job.shipper_id.name or ''
                consignee = service_job.consignee_id and service_job.consignee_id.name or ''
                estimated_revenue = service_job.estimated_revenue or ''
                estimated_cost = service_job.estimated_cost or ''

                service_total_charges = []
                service_charges_dict = {}
                service_actual_charges_dict = {}
                for revenue_charge in service_job.revenue_charge_ids:
                    if revenue_charge.product_id not in service_total_charges:
                        service_total_charges.append(revenue_charge.product_id)
                    if revenue_charge.product_id.display_name in service_charges_dict.keys():
                        if (revenue_charge.amount_currency_id in
                                service_charges_dict[revenue_charge.product_id.display_name].keys()):
                            service_charges_dict[revenue_charge.product_id.display_name][
                                revenue_charge.amount_currency_id]['amount'] += revenue_charge.total_currency_amount
                        else:
                            service_charges_dict[revenue_charge.product_id.display_name].update({
                                revenue_charge.amount_currency_id: {'amount': revenue_charge.total_currency_amount,
                                                                    'exchange_rate': revenue_charge.amount_conversion_rate,
                                                                    'currency_id': revenue_charge.amount_currency_id}})
                    else:
                        service_charges_dict.update({revenue_charge.product_id.display_name: {
                            revenue_charge.amount_currency_id: {'amount': revenue_charge.total_currency_amount,
                                                                'exchange_rate': revenue_charge.amount_conversion_rate,
                                                                'currency_id': revenue_charge.amount_currency_id}}})
                    if revenue_charge.product_id.display_name in service_actual_charges_dict.keys():
                        if (revenue_charge.amount_currency_id in
                                service_actual_charges_dict[revenue_charge.product_id.display_name].keys()):
                            service_actual_charges_dict[revenue_charge.product_id.display_name][
                                revenue_charge.amount_currency_id]['amount'] += revenue_charge.actual_invoiced_amount
                        else:
                            service_actual_charges_dict[revenue_charge.product_id.display_name].update({
                                revenue_charge.amount_currency_id: {'amount': revenue_charge.actual_invoiced_amount,
                                                                    'exchange_rate': revenue_charge.amount_conversion_rate,
                                                                    'currency_id': revenue_charge.amount_currency_id}})
                    else:
                        service_actual_charges_dict.update({revenue_charge.product_id.display_name: {
                            revenue_charge.amount_currency_id: {'amount': revenue_charge.actual_invoiced_amount,
                                                                'exchange_rate': revenue_charge.amount_conversion_rate,
                                                                'currency_id': revenue_charge.amount_currency_id
                                                                }}})
                service_cost_dict = {}
                service_actual_cost_dict = {}
                for revenue_cost in service_job.cost_charge_ids:
                    if revenue_cost.product_id not in service_total_charges:
                        service_total_charges.append(revenue_cost.product_id)
                    if revenue_cost.product_id.display_name in service_cost_dict.keys():
                        if (revenue_cost.amount_currency_id in
                                service_cost_dict[revenue_cost.product_id.display_name].keys()):
                            service_cost_dict[revenue_cost.product_id.display_name][
                                revenue_cost.amount_currency_id]['amount'] += revenue_cost.total_currency_amount
                        else:
                            service_cost_dict[revenue_cost.product_id.display_name].update({
                                revenue_cost.amount_currency_id: {'amount': revenue_cost.total_currency_amount,
                                                                  'exchange_rate': revenue_cost.amount_conversion_rate,
                                                                  'currency_id': revenue_cost.amount_currency_id
                                                                  }})
                    else:
                        service_cost_dict.update({revenue_cost.product_id.display_name: {
                            revenue_cost.amount_currency_id: {'amount': revenue_cost.total_currency_amount,
                                                              'exchange_rate': revenue_cost.amount_conversion_rate,
                                                              'currency_id': revenue_cost.amount_currency_id}}})
                    if revenue_cost.product_id.display_name in service_actual_cost_dict.keys():
                        if (revenue_cost.amount_currency_id in
                                service_actual_cost_dict[revenue_cost.product_id.display_name].keys()):
                            service_actual_cost_dict[revenue_cost.product_id.display_name][
                                revenue_cost.amount_currency_id]['amount'] += revenue_cost.actual_billed_amount
                        else:
                            service_actual_cost_dict[revenue_cost.product_id.display_name].update({
                                revenue_cost.amount_currency_id: {'amount': revenue_cost.actual_billed_amount,
                                                                  'exchange_rate': revenue_cost.amount_conversion_rate,
                                                                  'currency_id': revenue_cost.amount_currency_id
                                                                  }})
                    else:
                        service_actual_cost_dict.update({revenue_cost.product_id.display_name: {
                            revenue_cost.amount_currency_id: {'amount': revenue_cost.actual_billed_amount,
                                                              'exchange_rate': revenue_cost.amount_conversion_rate,
                                                              'currency_id': revenue_cost.amount_currency_id}}})
                final_dict_actual = {}
                for key, value in service_charges_dict.items():
                    final_dict_actual[key] = {}
                    for key, value in service_charges_dict.items():
                        final_dict_actual[key] = {}
                        for currency, charge in value.items():
                            cost_data = service_actual_charges_dict.get(key, {}).get(currency)
                            cost_amount = cost_data['amount'] if cost_data and 'amount' in cost_data else 0
                            final_dict_actual[key][currency] = {'charge': charge['amount'], 'cost': cost_amount,
                                                         'exchange_rate': charge['exchange_rate']}
                    for key, value in service_actual_charges_dict.items():
                        if key not in final_dict_actual:
                            final_dict_actual[key] = {}
                        for currency, cost in value.items():
                            if currency not in final_dict_actual.get(key, {}):
                                final_dict_actual[key][currency] = {'charge': 0, 'cost': cost['amount'],
                                                                    'exchange_rate': cost['exchange_rate']}
                for charge in final_dict_actual:
                    for currency_vise_charge in final_dict_actual[charge]:
                        charge_code = charge or ''
                        charge_string = charge.split(' ')
                        charge_name = ' '.join(charge_string[1:]) if '[' in charge_string[0] else ' '.join(
                            charge_string) or ''
                        estimated_revenue_cost_currency = currency_vise_charge.symbol
                        estimated_revenue = final_dict_actual[charge][currency_vise_charge].get('charge') # service_charges_dict.get(charge.display_name) or 0.0
                        estimated_cost = final_dict_actual[charge][currency_vise_charge].get('cost') # service_cost_dict.get(charge.display_name) or 0.0
                        # estimated_profit = estimated_revenue - estimated_cost
                        estimated_profit = (estimated_revenue * final_dict_actual[charge][currency_vise_charge]
                                            .get('exchange_rate')) - (estimated_cost *
                                                                      final_dict_actual[charge][currency_vise_charge]
                                                                      .get('exchange_rate'))

                        service_charge = False
                        service_currency_vise_charge = False
                        service_currency = False
                        if service_actual_charges_dict and service_actual_charges_dict.get(charge):
                            service_charge = service_actual_charges_dict.get(charge)
                            if service_charge and service_charge.get(currency_vise_charge):
                                service_currency_vise_charge = service_charge.get(currency_vise_charge, {'currency_id': False})
                                service_currency = service_currency_vise_charge.get('currency_id')

                        actual_revenue = service_charge and service_currency_vise_charge and service_currency_vise_charge.get('amount', 0) or 0.0
                        actual_revenue_currency = service_charge and service_currency_vise_charge and service_currency and service_currency.symbol or ''
                        actual_cost = service_charge and service_currency_vise_charge and service_currency_vise_charge.get('amount', 0) or 0.0
                        if service_charge and service_currency_vise_charge:
                            actual_cost_currency = service_currency and service_currency.symbol
                        else:
                            actual_cost_currency = [key.symbol for key in final_dict_actual[charge].keys()][0]
                        actual_cost_exchange_rate = service_charge and service_currency_vise_charge and service_currency_vise_charge.get('exchange_rate', 1) or 1
                        # actual_profit = actual_revenue - actual_cost
                        exchange_rate = service_charge and service_currency_vise_charge and service_currency_vise_charge.get('exchange_rate', 1) or 1
                        actual_profit = (actual_revenue * exchange_rate - actual_cost * exchange_rate)

                        service_jobs_list.append({
                            'company_id': company_id,
                            'transport_mode': transport_mode,
                            'shipment_type': shipment_type,
                            'cargo_type': cargo_type,
                            'booking_nomination_no': booking_nomination_no,
                            'date': date,
                            'shipment_service_job': shipment_service_job,
                            'sales_agent': sales_agent,
                            'customer': customer,
                            'shipper': shipper,
                            'consignee': consignee,
                            'charge_code': charge_code,
                            'charge_name': charge_name,
                            'estimated_revenue': estimated_revenue,
                            'estimated_revenue_cost_currency': estimated_revenue_cost_currency,
                            'estimated_revenue_in_company_currency': estimated_revenue * final_dict_actual[charge][
                                                                         currency_vise_charge].get('exchange_rate'),
                            'estimated_cost': estimated_cost,
                            'estimated_cost_in_company_currency': estimated_cost * final_dict_actual[charge][
                                currency_vise_charge].get('exchange_rate'),
                            'estimated_profit': estimated_profit,
                            'actual_revenue': actual_revenue,
                            'actual_revenue_currency': actual_revenue_currency,
                            'actual_revenue_exchange_rate': service_charge and service_currency_vise_charge and service_currency_vise_charge.get('exchange_rate', 1),
                            'actual_revenue_in_company_currency': (service_charge and service_currency_vise_charge and service_currency_vise_charge.get('exchange_rate', 1) or 1) * actual_revenue,
                            'actual_cost': actual_cost,
                            'actual_cost_currency': actual_cost_currency,
                            'actual_cost_exchange_rate': actual_cost_exchange_rate,
                            'actual_cost_in_company_currency': actual_cost_exchange_rate * actual_cost,
                            'actual_profit': actual_profit * actual_cost_exchange_rate,
                            'exchange_rate': final_dict_actual[charge][currency_vise_charge].get('exchange_rate')
                        })

        def groupby_function(d):
            return d['date']

        all_shipments_list = []
        for distinct_values, groupby_res in groupby(sorted(shipments_list + service_jobs_list, key=groupby_function), groupby_function):
            result = list(groupby_res)
            for res in result:
                all_shipments_list.append(res)

        self.xlsx_report_data(worksheet, line_style, all_shipments_list)

        workbook.close()
        filename = 'Charge Wise Shipment Estimated VS Actual %s-%s' % (self.from_date.strftime('%d%b%Y'), self.to_date.strftime('%d%b%Y'))
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

    def xlsx_report_data(self, worksheet, line_style, shipments_list):
        row = 1
        col = 0
        for shipment_list in shipments_list:
            worksheet.write(row, col, shipment_list.get('company_id'), line_style)
            worksheet.write(row, col+1, shipment_list.get('transport_mode'), line_style)
            worksheet.write(row, col+2, shipment_list.get('shipment_type'), line_style)
            worksheet.write(row, col+3, shipment_list.get('cargo_type'), line_style)
            worksheet.write(row, col+4, shipment_list.get('booking_nomination_no'), line_style)
            worksheet.write(row, col+5, shipment_list.get('date'), line_style)
            worksheet.write(row, col+6, shipment_list.get('shipment_service_job'), line_style)
            worksheet.write(row, col+7, shipment_list.get('sales_agent'), line_style)
            worksheet.write(row, col+8, shipment_list.get('customer'), line_style)
            worksheet.write(row, col+9, shipment_list.get('shipper'), line_style)
            worksheet.write(row, col+10, shipment_list.get('consignee'), line_style)
            worksheet.write(row, col+11, shipment_list.get('charge_code'), line_style)
            worksheet.write(row, col+12, shipment_list.get('charge_name'), line_style)
            worksheet.write(row, col+13, round(shipment_list.get('estimated_revenue') or 0, 2), line_style)
            worksheet.write(row, col+14, shipment_list.get('estimated_revenue_cost_currency'), line_style)
            worksheet.write(row, col+15, shipment_list.get('exchange_rate'), line_style)
            worksheet.write(row, col+16, round(shipment_list.get('estimated_revenue_in_company_currency') or 0, 2), line_style)
            worksheet.write(row, col+17, round(shipment_list.get('estimated_cost') or 0, 2), line_style)
            worksheet.write(row, col+18, shipment_list.get('estimated_revenue_cost_currency'), line_style)
            worksheet.write(row, col+19, shipment_list.get('exchange_rate'), line_style)
            worksheet.write(row, col+20, round(shipment_list.get('estimated_cost_in_company_currency') or 0, 2), line_style)
            worksheet.write(row, col+21, round(shipment_list.get('estimated_profit') or 0, 2), line_style)
            worksheet.write(row, col+22, round(shipment_list.get('actual_revenue') or 0, 2), line_style)
            worksheet.write(row, col+23, shipment_list.get('actual_revenue_currency'), line_style)
            worksheet.write(row, col+24, shipment_list.get('actual_revenue_exchange_rate'), line_style)
            worksheet.write(row, col+25, round(shipment_list.get('actual_revenue_in_company_currency') or 0, 2), line_style)
            worksheet.write(row, col+26, round(shipment_list.get('actual_cost') or 0, 2), line_style)
            worksheet.write(row, col+27, shipment_list.get('actual_cost_currency'), line_style)
            worksheet.write(row, col+28, shipment_list.get('actual_cost_exchange_rate'), line_style)
            worksheet.write(row, col+29, round(shipment_list.get('actual_cost_in_company_currency') or 0, 2), line_style)
            worksheet.write(row, col+30, round(shipment_list.get('actual_profit') or 0, 2), line_style)
            row = row + 1
            col = 0
