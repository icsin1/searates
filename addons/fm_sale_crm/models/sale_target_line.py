from odoo import models, fields, api


class CRMSaleTargetLine(models.Model):
    _name = "crm.sale.target.line"
    _description = "Sale Target Line"

    def get_house_shipment_domain(self):
        self.ensure_one()
        domain = [
            ('sales_agent_id', '=', self.sale_target_id.user_id.id),
            ('shipment_date', '>=', self.date_from),
            ('shipment_date', '<=', self.date_to),
            ('company_id', '=', self.sale_target_id.company_id.id)]
        if self.sale_target_id.shipment_type_id:
            domain += [('shipment_type_id', '=', self.sale_target_id.shipment_type_id.id)]
        if self.sale_target_id.transport_mode_id:
            domain += [('transport_mode_id', '=', self.sale_target_id.transport_mode_id.id)]
        if self.sale_target_id.cargo_type_id:
            domain += [('cargo_type_id', '=', self.sale_target_id.cargo_type_id.id)]
        return domain

    @api.depends('date_from', 'date_to', 'target_parameter', 'target_value', 'target_uom_id')
    def _compute_actual_value(self):
        for line in self:
            actual_value = 0
            target_uom_id = line.target_uom_id

            def convert_weight_actual_value(shipment):
                return shipment.gross_weight_unit_uom_id._compute_quantity(shipment.gross_weight_unit, target_uom_id)

            def convert_volume_actual_value(shipment):
                return shipment.volume_unit_uom_id._compute_quantity(shipment.volume_unit, target_uom_id)

            house_shipment_ids = self.env['freight.house.shipment'].search(line.get_house_shipment_domain())

            if line.target_parameter == "weight":
                actual_value = sum(list(map(convert_weight_actual_value, house_shipment_ids)))
            elif line.target_parameter == "volume":
                actual_value = sum(list(map(convert_volume_actual_value, house_shipment_ids)))
            elif line.target_parameter == "gross_revenue":
                actual_value = sum(house_shipment_ids.mapped('received_revenue'))
            elif line.target_parameter == "gross_margin":
                actual_value = sum(house_shipment_ids.mapped('received_margin'))
            elif line.target_parameter == "teu":
                fcl_house_shipment_ids = house_shipment_ids.filtered(lambda s: not s.cargo_is_package_group)
                actual_value = sum(fcl_house_shipment_ids.mapped('container_ids.no_of_teu'))
            line.actual_value = actual_value

    @api.depends('date_from', 'date_to')
    def _compute_period(self):
        for line in self:
            line.period = line.date_from.strftime('%b - %Y')

    sale_target_id = fields.Many2one('crm.sale.target', string="Sale Target", ondelete='cascade')
    period = fields.Char(compute="_compute_period", store=True)
    date_from = fields.Date()
    date_to = fields.Date()
    target_parameter = fields.Selection([
        ('weight', 'Weight'),
        ('volume', 'Volume'),
        ('gross_revenue', 'Gross Revenue'),
        ('gross_margin', 'Gross Margin'),
        ('teu', 'TEUs'),
    ], string="Target Parameter", required=True)
    target_value = fields.Float()
    target_uom_id = fields.Many2one('uom.uom', string="Target UoM")
    actual_value = fields.Float(compute="_compute_actual_value", store=True)
    target_currency_id = fields.Many2one("res.currency", string="Target Currency", default=lambda self: self.env.company.currency_id)
    user_id = fields.Many2one("res.users", related='sale_target_id.user_id', store=True)
    house_shipment_names = fields.Char(compute='_compute_house_shipment_names')

    def _compute_house_shipment_names(self):
        Shipment = self.env['freight.house.shipment']
        for line in self:
            line.house_shipment_names = ', '.join(Shipment.search(line.get_house_shipment_domain()).mapped('name'))

    @api.model
    def get_budget_data(self, domain=[], limit=None, offset=None, **kwargs):
        labels = []
        budget = []
        actual = []
        tableData = []
        context = kwargs.get('context', self.env.context)
        download = context.get('download')
        domain = [('target_parameter', '=', kwargs.get('filter')), ('sale_target_id.company_id', 'in', context.get('allowed_company_ids', []))]
        for line in self.with_context(**context).read_group(domain=domain, fields=['user_id'], groupby=['user_id']):
            agent = line.get('user_id') and line.get('user_id')[1] or 'Not Available'
            target_value = sum(self.search(line['__domain']).mapped('target_value'))
            actual_value = sum(self.search(line['__domain']).mapped('actual_value'))

            if download or kwargs.get('type') == 'table':
                values = {'Agent': agent, 'Target': target_value, 'Actual': actual_value}

                if kwargs.get('filter') in ['weight', 'volume']:
                    uom = self.search(line['__domain']).mapped('target_uom_id')
                    values.update({'UOM': uom and uom[0].display_name or 'Not Applicable'})

                tableData.append(values)
                continue

            labels.append(agent)
            budget.append(target_value)
            actual.append(actual_value)

        if download or kwargs.get('type') == 'table':
            return tableData[offset: limit]

        return {
            'labels': labels,
            'datasets': [
                {"label": "Budget", "backgroundColor": "blue", "data": budget},
                {"label": "Actual", "backgroundColor": "red", "data": actual}
            ],
        }
