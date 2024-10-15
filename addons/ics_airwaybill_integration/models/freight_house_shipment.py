from odoo import models, fields, api
import base64


class FreightHouseShipment(models.Model):
    _inherit = 'freight.house.shipment'

    is_air_transport = fields.Boolean(
        string='Is Air Transport',
        compute='_compute_air_transport'
    )

    @api.depends('transport_mode_id')
    def _compute_air_transport(self):
        self.is_air_transport = False
        for rec in self:
            if rec.transport_mode_id and rec.transport_mode_id.code.lower() == 'air':
                rec.is_air_transport = True

    def generate_file_content(self):
        self.ensure_one()
        slac = 4
        hbs_txt_lines = []
        for package in self.package_ids:
            remarks = " ".join(
                [commodity.remarks or '' for commodity in package.commodity_ids])
            hbs_txt_lines.append("HBS/{}/{}{}/{}/K{}/{}/{}".format(
                self.hbl_number,
                self.origin_port_un_location_id.code,
                self.destination_port_un_location_id.code,
                package.quantity,
                package.total_weight_unit,
                slac,
                remarks
            ))
            if package.hbl_description:
                hbs_txt_lines.append("TXT/{}".format(package.hbl_description))

        def format_line(template, *args):
            return (template.format(*args) + '\n').encode('utf-8') if all(args) else b''

        lines = [
            b"FHL/4\n",
            format_line("MBI/{}-{}{}{}/T{}K{}",
                        self.shipping_line_id.airline_prefix,
                        self.carrier_booking_reference_number,
                        self.origin_port_un_location_id.code,
                        self.destination_port_un_location_id.code,
                        self.pack_unit,
                        self.gross_weight_unit),
            ("\n".join(hbs_txt_lines) + "\n").encode('utf-8') if hbs_txt_lines else b"",
            format_line("OCI/{}/ISS/RA/00999-00",
                        self.customs_location_id.country_id.code),
            format_line("/{}/CNE/T/98-048888500",
                        self.consignee_id.country_id.code),
            format_line("/{}/CNE/CP/JO DYBEL",
                        self.consignee_id.country_id.code),
            format_line("/{}/CNE/CT/9056666314",
                        self.consignee_id.country_id.code),
            format_line("/{}/SHP/T/0",
                        self.customs_location_id.country_id.code),
            format_line("/{}/AGT/T/{}002288888B01", self.customs_location_id.country_id.code,
                        self.customs_location_id.country_id.code),
            b"SHP\n" if self.shipper_id else b'',
            format_line("NAM/{}", self.shipper_id.name),
            format_line("ADR/{} {}", self.shipper_id.street,
                        self.shipper_id.street2),
            format_line("LOC/{}", self.shipper_id.city_id.name),
            format_line("/{}/{} {}", self.shipper_id.country_id.code,
                        self.shipper_id.zip, self.shipper_id.state_id.code),
            b"CNE\n" if self.consignee_id else b'',
            format_line("NAM/{}", self.consignee_id.name),
            format_line("ADR/{} {}", self.consignee_id.street,
                        self.consignee_id.street),
            format_line("LOC/{}", self.consignee_id.city_id.name),
            format_line("/{}/{} {}", self.consignee_id.country_id.code,
                        self.consignee_id.zip, self.consignee_id.state_id.code)
        ]
        return b''.join(lines)

    def action_print(self):
        filename = '%s.snd' % (self.hbl_number)
        content = self.generate_file_content()
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
            })
        else:
            attachment.write({'datas': base64.b64encode(content)})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true&filename=%s' % (attachment.id, filename),
            'target': 'new',
        }
