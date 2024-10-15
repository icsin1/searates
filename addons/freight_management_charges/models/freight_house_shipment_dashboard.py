from odoo import tools, models, api, _, tools
from odoo.tools.float_utils import float_round
from odoo.tools import format_decimalized_amount, safe_eval


class FreightShipmentDashboard(models.Model):
    _inherit = 'freight.house.shipment'

    @api.model
    def get_shipment_by_tradelane_data(self, domain=[], limit=None, offset=0, count=False, **kwargs):
        """This function will return the Shipment Data based on the Trade Lane.

        Example:
        Tabular Data Returned as

        [{
            {
            "Origin": "AEJEA",
            "Destination": "LYBEN",
            "Shipment": 13,
            "TEUs": 21
            },
        }, ...]

        Args:
            domain (list, optional): Domain value received from the UI side. Defaults to list().
            limit (int, optional): No of Records to be loaded. Defaults to 10.
            offset (int, optional): Offset Value from which next records to be fetched. Defaults to 0.
            count (bool, optional): return whether to return only count. Defaults to False.

        Returns:
            List: Shipment Data based on the Trade Lane.
            OR
            Integer: Count of the Records for pagination view.
        """
        self = self.with_context(**kwargs.get('context', {}))
        tableData = []
        domain += [('state', '!=', 'cancelled')]

        FreightUnLocationObj = self.env['freight.un.location']
        lines = self.read_group(
            domain, ['shipment_ids:array_agg(id)', 'origin_un_location_id', 'destination_un_location_id:count'], ['origin_un_location_id', 'destination_un_location_id'], offset=offset, lazy=False)
        if count:
            return len(lines[offset: limit])
        for line in lines:
            count += 1
            origin_loc = _('Not Available')
            if line.get("origin_un_location_id") and line['origin_un_location_id'][0]:
                origin_loc = FreightUnLocationObj.browse(line['origin_un_location_id'][0]).with_context(prefetch_fields=False)
                origin_loc = origin_loc.loc_code or origin_loc
            destination_loc = _('Not Available')
            if line.get("destination_un_location_id") and line['destination_un_location_id'][0]:
                destination_loc = FreightUnLocationObj.browse(line['destination_un_location_id'][0]).with_context(prefetch_fields=False)
                destination_loc = destination_loc.loc_code or destination_loc

            tableData.append({
                'Origin': origin_loc,
                'Destination': destination_loc,
                'Shipment': line['__count'],
                'TEUs': sum(self.with_context(prefetch_fields=False).browse(line['shipment_ids']).mapped('teu_total'))
            })

        tableData.sort(key=lambda x: x['Shipment'], reverse=True)
        return tableData[offset: limit]

    @api.model
    def get_shipment_by_profitability_data(self, domain=list(), limit=10, offset=0, count=False, **kwargs):
        """Returns the Profitability Data for Shipment Dashboard where the data is grouped based on the Customer to have the Customer specific
        Revenue, Cost and Margin.

        Example:
        Tabular Data Returned as

        [{
            "Customer": "ABC TRADING PVT LTD",
            "Revenue": 0.0,
            "Cost": 1194.0,
            "Margin Amount": -1194.0,
            "Margin %": -100.0
        }, ...]

        Args:
            domain (list, optional): Domain value received from the UI side. Defaults to list().
            limit (int, optional): No of Records to be loaded. Defaults to 10.
            offset (int, optional): Offset Value from which next records to be fetched. Defaults to 0.
            count (bool, optional): return whether to return only count. Defaults to False.

        Returns:
            List: List of Profitability Data.
            OR
            Integer: Count of the Records for pagination view.
        """
        self = self.with_context(**kwargs.get('context', {}))
        tableData = []
        lines = self.read_group(domain, ['shipment_ids:array_agg(id)', 'client_id'], ['client_id'], limit=limit - offset if limit else 0, offset=offset, lazy=False)
        if count:
            return len(lines)

        shipment_ids_list = list()
        for line in lines:
            shipment_ids_list.extend(line['shipment_ids'])

        domain = [('house_shipment_id', 'in', shipment_ids_list)]
        Report = self.env['house.cost.revenue.report'].with_context(prefetch_fields=False)
        cost_revenue_data = Report.read_group(domain, ['house_shipment_id', 'revenue_total_amount:sum', 'cost_total_amount:sum', 'estimated_margin:sum'], ['house_shipment_id'], lazy=False)
        shipment_wise_revenue_data = dict([(d['house_shipment_id'][0], d['revenue_total_amount']) for d in cost_revenue_data])
        shipment_wise_cost_data = dict([(d['house_shipment_id'][0], d['cost_total_amount']) for d in cost_revenue_data])
        shipment_wise_margin_data = dict([(d['house_shipment_id'][0], d['estimated_margin']) for d in cost_revenue_data])
        for line in lines:
            total_estimated_margin = sum([shipment_wise_margin_data.get(shipment_id, 0.0) for shipment_id in line['shipment_ids']])
            total_estimated_cost = sum([shipment_wise_cost_data.get(shipment_id, 0.0) for shipment_id in line['shipment_ids']])
            try:
                total_estimated_margin_percentage = total_estimated_margin / total_estimated_cost * 100
            except ZeroDivisionError:
                total_estimated_margin_percentage = 0.00
            tableData.append({
                'Customer': line['client_id'][1] or 'Not Available',
                'Revenue': round(sum([shipment_wise_revenue_data.get(shipment_id, 0.0) for shipment_id in line['shipment_ids']]), 2),
                'Cost': round(total_estimated_cost, 2),
                'Margin Amount': round(total_estimated_margin, 2),
                'Margin %': round(total_estimated_margin_percentage, 2),
            })
        return tableData

    def _get_job_costsheet_total_by_field(self, domain, field):
        """Charges values based on the provided Filter for the field provided.

        Args:
            domain (List): List of domain filters
            field (String): Name of the Field

        Returns:
            Float: Cost/Revenue Charge Values.
        """
        allowed_company_ids = self._context.get('allowed_company_ids', [])
        if allowed_company_ids and hasattr(self, 'company_id'):
            domain += [['company_id', 'in', allowed_company_ids]]

        # Below code will ensure that the house shipment domain will work as it is with House Cost Revenue Report.
        for leaf in domain:
            if isinstance(leaf, list):
                sub_leaf = leaf[0].split(".")
                # TODO: try to improve the code.
                # ensure if the house shipment prefix is already there then do not add it again.
                if not (sub_leaf[0] == 'house_shipment_id'):
                    leaf[0] = f'house_shipment_id.{sub_leaf[0]}'
        Report = self.env['house.cost.revenue.report'].with_context(prefetch_fields=False)
        cost_revenue_data = Report.read_group(domain, [f'{field}:sum'], [], lazy=False)
        return cost_revenue_data[0][field] or 0.0

    @api.model
    def get_shipment_revenue_profitability_data(self, domain=[], **kwargs):
        self = self.with_context(**kwargs.get('context', {}))

        total_estimated_revenue = self._get_job_costsheet_total_by_field(domain, 'revenue_total_amount')
        return format_decimalized_amount(total_estimated_revenue, self.env.company.currency_id)

    @api.model
    def get_shipment_cost_profitability_data(self, domain=[], **kwargs):
        self = self.with_context(**kwargs.get('context', {}))

        total_estimated_cost = self._get_job_costsheet_total_by_field(domain, 'cost_total_amount')
        return format_decimalized_amount(total_estimated_cost, self.env.company.currency_id)

    @api.model
    def get_shipment_margin_profitability_with_per_data(self, domain=[], **kwargs):
        self = self.with_context(**kwargs.get('context', {}))
        total_estimated_margin = self._get_job_costsheet_total_by_field(domain, 'estimated_margin')
        formated_total_estimated_margin = format_decimalized_amount(total_estimated_margin, self.env.company.currency_id)
        percentage_total_estimated_margin = self.get_shipment_margin_per_profitability_data(domain=domain, **kwargs)
        return f'{formated_total_estimated_margin} ({percentage_total_estimated_margin}%)'

    @api.model
    def get_shipment_margin_profitability_data(self, domain=[], **kwargs):
        self = self.with_context(**kwargs.get('context', {}))
        total_estimated_margin = self._get_job_costsheet_total_by_field(domain, 'estimated_margin')
        formated_total_estimated_margin = format_decimalized_amount(total_estimated_margin, self.env.company.currency_id)
        return formated_total_estimated_margin

    @api.model
    def get_shipment_margin_per_profitability_data(self, domain=[], **kwargs):
        self = self.with_context(**kwargs.get('context', {}))
        total_estimated_margin = self._get_job_costsheet_total_by_field(domain, 'estimated_margin')
        total_estimated_cost = self._get_job_costsheet_total_by_field(domain, 'cost_total_amount')
        try:
            total_estimated_margin_percentage = total_estimated_margin / total_estimated_cost * 100
        except ZeroDivisionError:
            total_estimated_margin_percentage = 0.00
        return round(total_estimated_margin_percentage, 2)

    @api.model
    def get_shipment_total_volume(self, domain=[], **kwargs):
        """Total Shipment container Volume.

        Args:
            domain (List): List of domain filters.

        Returns:
            Float: Shipment Total Volume
        """
        self = self.with_context(**kwargs.get('context', {}))
        domain += [('container_ids', '!=', False), ('packaging_mode', '=', 'container')]
        house_shipment_ids = self.env['freight.house.shipment'].search(domain)
        uom_cubic_meter_id = self.env.company.volume_uom_id
        total_volume = 0.00
        for house_shipment in house_shipment_ids:
            for container in house_shipment.container_ids:
                if container.volume_unit_uom_id and container.volume_unit_uom_id.id != uom_cubic_meter_id.id:
                    total_volume += container.volume_unit_uom_id._compute_quantity(container.volume_unit, uom_cubic_meter_id, round=False)
                else:
                    total_volume += container.volume_unit
        return float_round(total_volume, precision_rounding=uom_cubic_meter_id.rounding)

    @api.model
    def get_shipment_total_teu(self, domain=[], **kwargs):
        """Provide the Total TEU count for the selected filter.

        Args:
            domain (List): List of domain filters

        Returns:
            Integer: Total TEU for the selected Filter.
        """
        self = self.with_context(**kwargs.get('context', {}))
        domain += [('container_ids', '!=', False), ('packaging_mode', '=', 'container')]
        house_shipment_ids = self.env['freight.house.shipment'].with_context(prefetch_fields=False).search(domain)
        total_teu = 0.00
        ContainerPackage = self.env['freight.house.shipment.package']
        data = ContainerPackage.read_group([('shipment_id', 'in', house_shipment_ids.ids)], ['no_of_teu:sum'], 'shipment_id')
        mapped_data = dict([(d['shipment_id'][0], d['no_of_teu']) for d in data if (d and d['shipment_id'])])
        for house_shipment in house_shipment_ids:
            total_teu += mapped_data.get(house_shipment.id, 0)
        return total_teu
