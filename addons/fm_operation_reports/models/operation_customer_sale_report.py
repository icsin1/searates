# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.tools import format_date


class OperationCustomerSaleReport(models.Model):
    _name = 'operation.customer.sale.report'
    _inherit = 'account.finance.report.mixin'
    _description = 'Operation: Customer Sales Report'

    def get_title(self):
        return _('Sales Report by Customer')

    def get_account_report_data(self, options, **kwargs):
        self.has_date_range = True
        values = super().get_account_report_data(options, **kwargs)
        values['sections'] = self.get_sorted(options, self._get_sections(options, **kwargs))
        return values

    def _get_options(self, options, **kwargs):
        options = super()._get_options(options, **kwargs)
        options['sortable'] = True
        options['filters'] = {
            'partner_ids': {
                'string': _('Customer'),
                'res_model': 'res.partner',
                'res_field': 'partner_ids',
                'res_ids': options.get('partner_ids', [])
            }
        }
        return options

    def _get_column_headers_properties(self, options, **kwargs):
        return {}

    def _get_column_headers(self, options, **kwargs):
        report_header = [
            _('TEU'),
            _('Sales'),
            _('Cost'),
            _('Profit'),
            _('Profit (%)'),
            _('Collection % (Incl. Tax)')]
        position = 0
        for report_label in self.get_operation_dynamic_report_header_record_ids():
            report_header.insert(position, report_label.name)
            position += 1
        return report_header

    def _generate_domain(self, options, **kwargs):
        dates = options.get('date', {})
        date_to = dates.get('date_to', fields.Date().today())
        date_from = dates.get('date_from', fields.Date.start_of(fields.Date.from_string(date_to), 'year'))
        domain = [('shipment_date', '>=', date_from), ('shipment_date', '<=', date_to)]
        return domain

    def _get_sales_values(self, domain, fields, group_by_fields):
        return self.env['house.shipment.sales.report'].sudo().read_group(domain, fields, group_by_fields)

    def _get_sales(self, domain):
        return self.env['house.shipment.sales.report'].sudo().search(domain)

    def get_line_vals(self, group, options, container_count, company_ids):
        shipment_package = self.env['freight.house.shipment.package'].sudo()

        revenue_amount = group.get('revenue_amount', 0.0)
        cost_amount = group.get('cost_amount', 0.0)
        profit_amount = revenue_amount - cost_amount
        line_percentage = round((profit_amount or 0) / (revenue_amount or 1) * 100, 3)
        line_collection = round(group.get('received_amount', 0.0) / (revenue_amount or 1.0) * 100, 3)

        record = {
            'Sales': (revenue_amount, self._format_currency(revenue_amount)),
            'Cost': (cost_amount, self._format_currency(cost_amount)),
            'Profit': (profit_amount, self._format_currency(profit_amount)),
            'Profit (%)': (line_percentage, '{} %'.format(line_percentage)),
            'Collection % (Incl. Tax)': (line_collection, f'{line_collection} %')
        }

        result = {}
        line_data = {}
        if group.get('partner_id'):
            shipment_pack_ids = shipment_package.search([
                ('shipment_id.company_id', 'in', company_ids),
                ('shipment_id.shipment_date', '>=', options.get('date').get('date_from')),
                ('shipment_id.shipment_date', '<=', options.get('date').get('date_to')),
                ('shipment_id.revenue_charge_ids.partner_id', '=', group.get('partner_id')[0])])

            for dynamic_colum in self.get_operation_dynamic_report_header_record_ids():
                if group.get('partner_id')[0] in shipment_pack_ids.shipment_id.client_id.ids:
                    line_count = len(shipment_pack_ids.filtered(lambda ln: ln.container_type_id.id in dynamic_colum.container_type_ids.ids))
                else:
                    line_count = 0
                container_count.append({dynamic_colum.name: line_count})
                line_data.update({dynamic_colum.name: (line_count or 0, line_count or 0)})

            if group.get('partner_id')[0] in shipment_pack_ids.shipment_id.client_id.ids:
                total_teus = sum(shipment_pack_ids.mapped('no_of_teu'))
            else:
                total_teus = 0

            line_data.update({'TEU': (total_teus, total_teus)})
            container_count.append({'TEU': (total_teus)})
            line_data.update(record)

        if group.get('company_id'):
            for contain in container_count:
                for key in contain.keys():
                    result[key] = result.get(key, 0) + contain[key]
            for key, val in result.items():
                line_data.update({key: (val or 0, val or 0)})
            line_data.update(record)
        return line_data

    def _get_sections(self, options, **kwargs):
        records = []
        container_count = []
        company_ids = self.env.context.get('allowed_company_ids', [])
        partner_domain = [
            ('partner_id', '!=', False),
            ('company_id', 'in', company_ids),
        ]
        fields = ['revenue_amount', 'cost_amount', 'received_amount', 'invoiced_amount']
        data_domain = partner_domain + self._generate_domain(options, **kwargs)

        if options.get('partner_ids'):
            data_domain += [('partner_id', 'in', options.get('partner_ids'))]
        groups = self._get_sales_values(data_domain, fields, ['partner_id'])
        container_count = []
        records += [{
            'id': group.get('partner_id')[0],
            'title': group.get('partner_id')[1],
            'code': group.get('partner_id')[0],
            'level': 1,
            'group_by': 'partner_id',
            'values': self.get_line_vals(group, options, container_count, company_ids),
        } for group in groups]
        records = self.get_sorted(options, records, True)

        # Overall
        groups = self._get_sales_values(data_domain, fields, ['company_id'])
        result = {}
        for line in groups:
            for key in line.keys():
                if key in fields:
                    result[key] = result.get(key, 0) + line[key]
        result.update({'company_id': self.env.context.get('allowed_company_ids', [])})
        records.append({
            'id': 'total',
            'title': _('Total'),
            'code': 'total',
            'level': 0,
            'group_by': False,
            'values': self.get_line_vals(result, options, container_count, company_ids),
        })
        return records

    def get_account_report_section_data(self, parent, options, **kwargs):
        partner_domain = [('partner_id', '=', parent.get('id'))]
        if self.env.context.get('allowed_company_ids', []):
            partner_domain += [('company_id', 'in', self.env.context.get('allowed_company_ids', []))]
        data_domain = partner_domain + self._generate_domain(options, **kwargs)

        if options.get('partner_ids'):
            data_domain += [('partner_id', 'in', options.get('partner_ids'))]

        data_fields = ['shipment_date', 'revenue_amount', 'cost_amount', 'received_amount', 'invoiced_amount']
        records = []
        for group in self._get_sales_values(data_domain, data_fields, ['shipment_id']):
            shipment = self.env['freight.house.shipment'].sudo().browse(group.get('shipment_id')[0])
            line_data = {
                'id': shipment.id,
                'title': shipment.display_name,
                'code': shipment.id,
                'level': 2,
                'house_bl_no': shipment.display_name,
                'row_class': 'font-weight-normal',
                'group_by': False,
                'values': {
                    'Shipment Date': (format_date(self.env, shipment.shipment_date))
                }
            }

            ShipmentPackage = self.env['freight.house.shipment.package'].sudo()
            shipment_packages = ShipmentPackage.search([('shipment_id', '=', shipment.id), ('shipment_id.client_id', '=', parent.get('id'))])
            for dynamic_colum in self.get_operation_dynamic_report_header_record_ids():
                line_count = len(shipment_packages.filtered(lambda ln: ln.container_type_id.id in dynamic_colum.container_type_ids.ids))
                line_data['values'][dynamic_colum.name] = (line_count or 0, line_count or 0)

            revenue_amount = group.get('revenue_amount', 0.0)
            cost_amount = group.get('cost_amount', 0.0)
            profit_amount = revenue_amount - cost_amount

            line_percentage = round((profit_amount or 0) / (revenue_amount or 1) * 100, 3)
            line_collection = round(group.get('received_amount', 0.0) / (revenue_amount or 1.0) * 100, 3)

            no_of_teus = sum(shipment_packages.mapped('no_of_teu'))

            line_data.get('values').update({
                'TEU': (no_of_teus, no_of_teus),
                'Sales': (revenue_amount, self._format_currency(revenue_amount)),
                'Cost': (cost_amount, self._format_currency(cost_amount)),
                'Profit': (profit_amount, self._format_currency(profit_amount)),
                'Profit (%)': (line_percentage, '{} %'.format(line_percentage)),
                'Collection % (Incl. Tax)': (line_collection, '{} %'.format(line_collection)),
            })
            records.append(line_data)
        return self.get_sorted(options, records, True)

    def get_operation_dynamic_report_header_record_ids(self):
        return self.env.company.container_size_ids

    def action_open_house(self, house_id, options, **kwargs):
        action = self.env["ir.actions.act_window"]._for_xml_id("freight_management.freight_shipment_house_action")
        form_view = [(self.env.ref('freight_management.freight_house_shipment_view_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = house_id
        return action
