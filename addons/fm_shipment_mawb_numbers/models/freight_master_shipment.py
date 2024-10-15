from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FreightMasterShipment(models.Model):
    _inherit = "freight.master.shipment"

    mawb_stock_line_ids = fields.One2many('mawb.stock.line', 'master_shipment_id', string="MAWB Stocks")
    mawb_stock_line_id = fields.Many2one('mawb.stock.line', string="MAWB Stock")

    @api.onchange('mawb_stock_line_id')
    def _onchange_mawb_number(self):
        if self.mawb_stock_line_id:
            self.update({'carrier_booking_reference_number': self.mawb_stock_line_id.display_name})

    def get_mawb_stock_line_domain(self):
        return [
            ('mawb_stock_id.airline_id', '=', self.shipping_line_id.id),
            ('mawb_stock_id.home_airport_id', '=', self.origin_port_un_location_id.id),
            ('status', '=', 'available'),
        ]

    def fetch_mawb_stocks(self):
        self.ensure_one()
        self.flush()
        if not self.shipping_line_id:
            raise ValidationError(_("Please select an Airline under Carriage section."))
        return {
            'name': 'Select MAWB Stock',
            'type': 'ir.actions.act_window',
            'res_model': 'mawb.stock.line',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[self.env.ref('fm_shipment_mawb_numbers.view_mawb_stock_line_tree_selection').id, 'list']],
            'domain': self.get_mawb_stock_line_domain(),
            'context': {
                'create': 0,
                'select': 1,
                'default_master_shipment_id': self.id,
            },
            'target': 'new',
        }

    def add_mawb_stocks(self):
        self.ensure_one()
        if not self.shipping_line_id:
            raise ValidationError(_("Please select an Airline under Carriage section."))
        action = self.env["ir.actions.actions"]._for_xml_id("fm_mawb_numbers.action_mawb_stock")
        action['target'] = 'new'
        action['views'] = [[self.env.ref('fm_mawb_numbers.view_mawb_stock_form').id, 'form']]
        action['context'] = {
            'default_master_shipment_id': self.id,
            'default_home_airport_id': self.origin_port_un_location_id.id,
            'default_airline_id': self.shipping_line_id.id,
            'wizard_save': 1,
        }
        return action

    #as after our new logic to m2o selection of mawb stock line, this method seems useless.
    def update_mawb_stocks(self):
        self.ensure_one()
        invalid_mawb_stock_line_ids = self.mawb_stock_line_ids.filtered(lambda line: line.mawb_stock_id.airline_id != self.shipping_line_id or line.mawb_stock_id.home_airport_id != self.origin_port_un_location_id)
        if invalid_mawb_stock_line_ids:
            invalid_mawb_stock_line_ids.write({
                'status': 'available',
            })
            remove_mawb_stock_line_ids = [(3, line.id) for line in invalid_mawb_stock_line_ids]
            self.write({
                'mawb_stock_line_ids': remove_mawb_stock_line_ids
            })

    def update_mawb_stock_line(self):
        self.ensure_one()
        mawb_stock_line_id = self.mawb_stock_line_id
        mawb_stock_id = mawb_stock_line_id and mawb_stock_line_id.mawb_stock_id or False
        if mawb_stock_id and (mawb_stock_id.airline_id != self.shipping_line_id or mawb_stock_id.home_airport_id != self.origin_port_un_location_id):
            self.write({'mawb_stock_line_id':False})
        return

    @api.model_create_single
    def create(self, values):
        res = super().create(values)
        if 'shipping_line_id' in values or 'origin_port_un_location_id' in values:
            res.update_mawb_stock_line()
        if 'carrier_booking_reference_number' in values and res.mode_type == 'air':
            res.onchange_carrier_booking_reference_number()
        return res

    def write(self, values):
        res = super().write(values)
        for shipment in self:
            if 'shipping_line_id' in values or 'origin_port_un_location_id' in values:
                shipment.update_mawb_stock_line()
        return res

    @api.onchange('carrier_booking_reference_number', 'mode_type', 'shipping_line_id', 'origin_port_un_location_id')
    def onchange_carrier_booking_reference_number(self):
        if self.mode_type == 'air' and self.carrier_booking_reference_number and not self.env.company.skip_mawb_validations:
            if self.mode_type == 'air' and not self.origin_port_un_location_id:
                raise ValidationError(_("Please add 'Origin Airport' for this shipment and Then add MAWB number(Remove the MAWB number for now.)."))
            mawb_stock_line_id = self.get_mawb_stock_line(self.carrier_booking_reference_number, self.shipping_line_id.id, self.origin_port_un_location_id.id)
            if mawb_stock_line_id:
                self.mawb_stock_line_id = mawb_stock_line_id
            else:
                # if not found the existing MAWB number then will try to create one with existing logic
                mawb_number = self.carrier_booking_reference_number.replace('-','')
                if len(mawb_number) != 11:
                    raise ValidationError(_("MAWB Number must be 11 Digit or 12 Character long with hyphen(-)"))
                mawb_stock_line_id = self.create_new_mawb_stock_number(mawb_number, self.origin_port_un_location_id)
                if not mawb_stock_line_id:
                    raise ValidationError(_("Invalid MAWB Number, Can not create '%s' perticular MAWB number."%(self.carrier_booking_reference_number)))

    def get_mawb_stock_line(self, mawb_number, shipping_line_id, origin_port_un_location_id):
        result = []
        mawb_number = mawb_number.replace('-','')
        if mawb_number and shipping_line_id:
            query = """
                SELECT msl.id
                FROM mawb_stock_line msl
                inner join mawb_stock ms on msl.mawb_stock_id = ms.id
                inner join freight_carrier fc on ms.airline_id = fc.id
                inner join freight_port fp on ms.home_airport_id = fp.id
                WHERE regexp_replace(mawb_number, '[^0-9]', '', 'g') = '%s'
                    and fc.id = %s
                    and fp.id = %s
            """%(mawb_number,shipping_line_id,origin_port_un_location_id)
            self._cr.execute(query)
            result = self._cr.dictfetchall()
        if result and result[0]:
            return result[0].get('id',False)
        else:
            return False

    def create_new_mawb_stock_number(self, mawb_number, origin_port_un_location_id):
        if mawb_number and origin_port_un_location_id:
            if not mawb_number.isdigit():
                raise ValidationError(_("MAWB must have only numbers and hyphen(-).\nFor Example : '123-12345678' or '12312345678'."))
            mawb_stock_line_id = False
            awb_serial_no = mawb_number[3:-1]
            mawb_prefix = mawb_number[:3]
            airline_id = self.env['freight.carrier'].search([('airline_prefix', '=', mawb_prefix)], limit=1)
            if airline_id:
                self.shipping_line_id = airline_id.id
            else:
                raise ValidationError(_("No Airline found with '%s' Airline Prefix."%(mawb_prefix)))
            serial_no = int(awb_serial_no)
            new_number = str(serial_no)+str(serial_no%7)
            if new_number != mawb_number[3:]:
                mawb_stock_line_id = False
            else:
                values = {
                    'airline_id': airline_id.id,
                    'home_airport_id': origin_port_un_location_id.id,
                    'awb_serial_no': awb_serial_no,
                    'count': 1,
                    'line_ids': [(0, 0, {
                                        'status': 'linked',
                                        'sequence_no': awb_serial_no})]
                }
                mawb_stock_id = self.env['mawb.stock'].create(values)
                mawb_stock_line_id = mawb_stock_id.line_ids[0].id
                self.write({
                        'mawb_stock_line_id': mawb_stock_line_id
                    })
                mawb_stock_id.line_ids.filtered(lambda x: x.status == 'available').unlink()
            return mawb_stock_line_id
