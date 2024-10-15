# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.tools import format_date


class OperationShippingLineReport(models.Model):
    _name = 'operation.customer.shipping.line.report'
    _inherit = 'account.finance.report.mixin'
    _description = 'Operation: Customer Shipping Lines (Period) Report'

    def get_title(self):
        return _('Sales Report by Shipping Lines')

    def get_account_report_data(self, options, **kwargs):
        self.has_date_range = True
        values = super().get_account_report_data(options, **kwargs)
        values['sections'] = self.get_sorted(options, self._get_sections(options, **kwargs))
        return values

    def _get_options(self, options, **kwargs):
        options = super()._get_options(options, **kwargs)
        options['sortable'] = True
        options['filters'] = {
            'shipping_line_id': {
                'string': _('Shipping Lines'),
                'res_model': 'freight.carrier',
                'res_field': 'shipping_line_id',
                'domain': [('transport_mode_id', '=', self.env.ref('freight_base.transport_mode_sea').id)],
                'res_ids': options.get('shipping_line_id', [])
            }
        }
        return options

    def _get_column_headers(self, options, **kwargs):
        report_header = [
            _('TEU'),
            _('Sales'),
            _('Cost'),
            _('Profit'),
            _('Profit (%)'),
            _('Collection % (Incl. Tax)'),
        ]
        position = 0
        for report_label in self.get_operation_dynamic_report_header_record_ids():
            report_header.insert(position, report_label.name)
            position += 1
        return report_header

    def _get_column_headers_properties(self, options, **kwargs):
        return {}

    def _generate_domain(self, options, **kwargs):
        dates = options.get('date', {})
        date_to = dates.get('date_to', fields.Date().today())
        date_from = dates.get('date_from', fields.Date.start_of(fields.Date.from_string(date_to), 'year'))
        domain = [('shipment_date', '>=', date_from), ('shipment_date', '<=', date_to)]
        return domain

    def _get_shipping_line_values(self, domain, fields, group_by_fields):
        return self.env['house.shipment.sales.report'].sudo().read_group(domain, fields, group_by_fields)

    def _get_sales(self, domain):
        return self.env['house.shipment.sales.report'].sudo().search(domain)

    def get_line_vals(self, group, options, shipping_line_count, company_ids):
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
        if group.get('shipping_line_id'):
            total_teus = 0
            shipment_pack_ids = shipment_package.search([
                ('package_mode', '!=', 'package'),
                ('shipment_id.revenue_charge_ids', '!=', False),
                ('shipment_id.company_id', 'in', company_ids),
                ('shipment_id.shipment_date', '>=', options.get('date').get('date_from')),
                ('shipment_id.shipment_date', '<=', options.get('date').get('date_to')),
                ('shipment_id.shipping_line_id', '=', group.get('shipping_line_id')[0])])
            for dynamic_colum in self.get_operation_dynamic_report_header_record_ids():
                line_count = len(shipment_pack_ids.filtered(lambda ln: ln.container_type_id.id in dynamic_colum.container_type_ids.ids))
                shipping_line_count.append({dynamic_colum.name: line_count})
                line_data.update({dynamic_colum.name: (line_count or 0, line_count or 0)})
                total_teus = sum(shipment_pack_ids.mapped('no_of_teu'))

            line_data.update({'TEU': (total_teus, total_teus)})
            shipping_line_count.append({'TEU': (total_teus)})
            line_data.update(record)

        if group.get('company_id'):
            for contain in shipping_line_count:
                for key in contain.keys():
                    result[key] = result.get(key, 0) + contain[key]
            for key, val in result.items():
                line_data.update({key: (val or 0, val or 0)})
            line_data.update(record)
        return line_data

    def _get_sections(self, options, **kwargs):
        records = []
        shipping_line_count = []
        company_ids = self.env.context.get('allowed_company_ids', [])
        shipping_line_domain = [
            ('shipment_id.packaging_mode', '!=', 'package'),
            ('shipping_line_id', '!=', False),
            ('company_id', 'in', company_ids),
            ('shipment_id.transport_mode_id', '=', self.env.ref('freight_base.transport_mode_sea').id),
        ]
        fields = ['revenue_amount', 'cost_amount', 'received_amount', 'invoiced_amount']
        data_domain = shipping_line_domain + self._generate_domain(options, **kwargs)

        if options.get('shipping_line_id'):
            data_domain += [('shipping_line_id', 'in', options.get('shipping_line_id'))]
        shipping_line_groups = self._get_shipping_line_values(data_domain, fields, ['shipping_line_id'])
        records += [{
            'id': shipping_line.get('shipping_line_id')[0],
            'title': shipping_line.get('shipping_line_id')[1],
            'code': shipping_line.get('shipping_line_id')[0],
            'level': 1,
            'group_by': 'shipping_line_id',
            'values': self.get_line_vals(shipping_line, options, shipping_line_count, company_ids),
        } for shipping_line in shipping_line_groups]

        # Overall
        groups = self._get_shipping_line_values(data_domain, fields, ['company_id'])
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
            'values': self.get_line_vals(result, options, shipping_line_count, company_ids),
        })
        return records

    def get_account_report_section_data(self, parent, options, **kwargs):
        shipping_line_domain = [('shipping_line_id', '=', parent.get('id')), ('shipment_id.transport_mode_id', '=', self.env.ref('freight_base.transport_mode_sea').id)]
        if self.env.context.get('allowed_company_ids', []):
            shipping_line_domain += [('company_id', 'in', self.env.context.get('allowed_company_ids', []))]
        data_domain = shipping_line_domain + self._generate_domain(options, **kwargs)

        if options.get('shipping_line_ids'):
            data_domain += [('shipping_line_id', 'in', options.get('shipping_line_ids'))]

        data_fields = ['shipment_date', 'revenue_amount', 'cost_amount', 'received_amount', 'invoiced_amount']
        records = []
        for group in self._get_shipping_line_values(data_domain, data_fields, ['shipment_id']):
            shipment = self.env['freight.house.shipment'].sudo().browse(group.get('shipment_id')[0])
            if shipment.packaging_mode != 'package':
                line_data = {
                    'id': shipment.id,
                    'title': shipment.display_name,
                    'code': shipment.id,
                    'level': 2,
                    'row_class': 'font-weight-normal',
                    'house_bl_no': shipment.display_name,
                    'group_by': False,
                    'values': {
                        'Shipment Date': (format_date(self.env, shipment.shipment_date))
                    }
                }

            ShipmentPackage = self.env['freight.house.shipment.package'].sudo()
            shipment_packages = ShipmentPackage.search([('shipment_id', '=', shipment.id), ('shipment_id.shipping_line_id', '=', parent.get('id'))])
            for dynamic_colum in self.get_operation_dynamic_report_header_record_ids():
                line_count = len(shipment_packages.filtered(lambda ln: ln.container_type_id.id in dynamic_colum.container_type_ids.ids))
                if shipment.packaging_mode != 'package':
                    line_data['values'][dynamic_colum.name] = (line_count or 0, line_count or 0)

            revenue_amount = group.get('revenue_amount', 0.0)
            cost_amount = group.get('cost_amount', 0.0)
            profit_amount = revenue_amount - cost_amount

            line_percentage = round((profit_amount or 0) / (revenue_amount or 1) * 100, 3)
            line_collection = round(group.get('received_amount', 0.0) / (revenue_amount or 1.0) * 100, 3)

            no_of_teus = sum(shipment_packages.mapped('no_of_teu'))
            if shipment.packaging_mode != 'package':
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
