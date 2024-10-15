from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TariffBuy(models.Model):
    _name = 'tariff.buy'
    _inherit = 'tariff.mixin'
    _description = 'Buy Tariff'

    tariff_name = fields.Char(compute='_compute_tariff_name', store=True, readonly=True)
    vendor_id = fields.Many2one(
        'res.partner', domain="[('parent_id', '=', False), ('category_ids.is_vendor', '=', True), '|', ('company_id', '=', company_id), ('company_id', '=', False)]", required=True,
        string="Vendor/Agent")
    line_ids = fields.One2many('tariff.buy.line', 'buy_tariff_id', string='Charges', copy=True, context={'active_test': False})
    active_charge_count = fields.Integer(compute='_compute_active_charge_count', string='No of Active Charges (Count)')
    pickup_country_id = fields.Many2one('res.country', string='Pickup Country', readonly=False)
    pickup_location_type_id = fields.Many2one('freight.location.type', string="Pickup Location Type")
    road_origin_un_location_id = fields.Many2one('freight.un.location', related="origin_un_location_id", readonly=False,
                                                 string="Origin ")
    origin_un_location_id = fields.Many2one("freight.un.location", string="Origin",
                                            domain="[('country_id', '=', origin_country_id)]")
    delivery_country_id = fields.Many2one('res.country', string='Delivery Country', readonly=False)
    delivery_location_type_id = fields.Many2one('freight.location.type', string="Delivery Location Type")
    road_destination_un_location_id = fields.Many2one('freight.un.location',
                                                      string="Destination ", readonly=False)
    destination_un_location_id = fields.Many2one('freight.un.location', readonly=True,
                                                 string="Destination")
    origin_port_un_location_id = fields.Many2one('freight.port', string='Origin Airport',
                                                 domain="[('country_id', '=', origin_country_id),('transport_mode_id', '=', transport_mode_id)]")
    destination_port_un_location_id = fields.Many2one('freight.port', string='Destination Airport',
                                                      domain="[('country_id', '=', destination_country_id),('transport_mode_id', '=', transport_mode_id)]")

    @api.onchange('company_id')
    def onchange_company(self):
        self.update({
            'vendor_id': False,
            'line_ids': False
        })

    @api.constrains('shipment_type_id', 'transport_mode_id', 'cargo_type_id', 'origin_id', 'destination_id', 'vendor_id', 'road_origin_un_location_id', 'road_destination_un_location_id')
    def _check_buy_tariff_combination(self):
        for rec in self:
            domain = rec.get_buy_tariff_combination_domain()
            len_recs = self.search_count(domain)
            if len_recs > 1:
                raise ValidationError(_('%s already defined with same Buy tariff criteria!') % (rec.tariff_name))

    def get_buy_tariff_combination_domain(self):
        domain = [('shipment_type_id', '=', self.shipment_type_id.id), ('transport_mode_id', '=', self.transport_mode_id.id), ('cargo_type_id', '=', self.cargo_type_id.id),
                  ('vendor_id', '=', self.vendor_id.id), ('company_id', '=', self.company_id.id)]
        if self.transport_mode_type == 'land':
            domain += [('road_origin_un_location_id', '=', self.road_origin_un_location_id.id), ('road_destination_un_location_id', '=', self.road_destination_un_location_id.id)]
        else:
            domain += [('origin_id', '=', self.origin_id.id), ('destination_id', '=', self.destination_id.id)]
        return domain

    @api.depends('vendor_id', 'shipment_type_id', 'transport_mode_id', 'cargo_type_id', 'origin_id', 'destination_id', 'road_origin_un_location_id', 'road_destination_un_location_id')
    def _compute_tariff_name(self):
        for rec in self.filtered(lambda tb: tb.tariff_for == 'shipment'):
            location_suffix = ''
            if rec.origin_id:
                location_suffix = '-{}'.format(rec.origin_id.loc_code)
            if rec.destination_id:
                location_suffix = '{}-{}'.format(location_suffix, rec.destination_id.loc_code)
            if rec.road_origin_un_location_id:
                location_suffix = '-{}'.format(rec.road_origin_un_location_id.loc_code)
            if rec.road_destination_un_location_id:
                location_suffix = '{}-{}'.format(location_suffix, rec.road_destination_un_location_id.loc_code)
            rec.tariff_name = '{}-{}{}{}{}'.format(
                rec.vendor_id.name or '',
                rec.shipment_type_id.code or '',
                rec.transport_mode_id.code or '',
                rec.cargo_type_id.code or '',
                location_suffix
            )

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self):
        for rec in self:
            rec.currency_id = rec.vendor_id.currency_id.id

    def _get_active_charges(self, records, date=None):
        today = date or fields.Date.today()
        return records.filtered_domain([
            '|',
            ('date_from', '=', False),
            ('date_from', '<=', today),
            '|',
            ('date_to', '=', False),
            ('date_to', '>=', today)
        ])

    @api.depends('line_ids')
    def _compute_active_charge_count(self):
        for rec in self:
            active_charges = self._get_active_charges(rec.line_ids)
            rec.active_charge_count = len(active_charges)

    def action_import_charges(self):
        self.ensure_one()
        context = self._context.copy()
        context.update(default_res_id=self.id, default_res_model=self._name, default_company_id=self.company_id.id)
        return {
            'name': 'Fetch Charge Master',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.charge.master.fetch',
            'context': context,
        }

    def action_remove_charges(self):
        self.line_ids.unlink()

    def excel_write_charge_lines(self, workbook, worksheet):
        self.ensure_one()
        cell_right = workbook.add_format({'align': 'right', 'valign': 'vcenter'})
        cell_left = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
        date_format = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'num_format': 'yyyy/mm/dd'})
        for row, charge in enumerate(self.line_ids):
            worksheet.write(row + 1, 0, row + 1, cell_right)
            worksheet.write(row + 1, 1, charge.charge_type_id.name, cell_left)
            worksheet.write(row + 1, 2, charge.unit_price or '', cell_right)
            worksheet.write(row + 1, 3, charge.currency_id.name, cell_left)
            worksheet.write(row + 1, 4, charge.measurement_basis_id.name, cell_left)
            worksheet.write(row + 1, 5, charge.date_from and charge.date_from.strftime("%Y/%m/%d") or '', date_format)
            worksheet.write(row + 1, 6, charge.date_to and charge.date_to.strftime("%Y/%m/%d") or '', date_format)

    def update_create_tariff_line(self, charge_type, unit_price, currency, measurement, valid_from, valid_to):
        self.ensure_one()
        TariffBuyLineObj = self.env['tariff.buy.line']
        vals = {
            'charge_type_id': charge_type.id, 'unit_price': unit_price, 'currency_id': currency.id, 'measurement_basis_id': measurement.id,
            'date_from': valid_from, 'date_to': valid_to, 'buy_tariff_id': self.id,
        }
        buy_line = TariffBuyLineObj.search([('charge_type_id', '=', charge_type.id), ('buy_tariff_id', '=', self.id)], limit=1)
        if buy_line:
            buy_line.write(vals)
        else:
            buy_line = TariffBuyLineObj.create(vals)


class TariffBuyLine(models.Model):
    _name = 'tariff.buy.line'
    _inherit = 'tariff.mixin.line'
    _description = 'Tariff Buy Line'

    buy_tariff_id = fields.Many2one('tariff.buy', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', related='buy_tariff_id.company_id', store=True)
    transport_mode_id = fields.Many2one('transport.mode', related='buy_tariff_id.transport_mode_id', store=True)
    cargo_type_id = fields.Many2one('cargo.type', related='buy_tariff_id.cargo_type_id', store=True)
    transport_mode_type = fields.Selection(related='buy_tariff_id.transport_mode_type', store=True)
    active = fields.Boolean(related='buy_tariff_id.active', store=True)

    is_cargo_type = fields.Boolean(compute='_compute_is_cargo_type')

    @api.depends('measurement_basis_id', 'cargo_type_id')
    def _compute_is_cargo_type(self):
        """
        Compute method to determine if the Cargo type is 'FCL'.
        If the Cargo type is 'FCL',  is_cargo_type will be True OR False
        """
        for rec in self:
            rec.is_cargo_type = rec.cargo_type_id and rec.cargo_type_id == self.env.ref('freight_base.cargo_type_sea_fcl')

    @api.onchange('charge_type_id')
    def _onchange_charge_type_id(self):
        for line in self.buy_tariff_id.line_ids:
            if self.charge_type_id:
                lines = self.buy_tariff_id.line_ids.filtered(lambda x: x.charge_type_id.id == self.charge_type_id.id)
                if len(lines) > 1:
                    raise ValidationError(_('Charge type: %s is already added') % self.charge_type_id.name)
