# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.tools.misc import format_date


class ShipmentProfit(models.AbstractModel):
    _name = 'report.fm_operation_reports.report_shipment_profit'
    _description = 'Shipment Profit Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        ctx = data.get('context')
        active_id = ctx.get('active_id')
        docs = self.env['shipment.profit.report'].browse(active_id)
        domain = [('shipment_date', '>=', docs.from_date), ('shipment_date', '<=', docs.to_date)]
        if docs.transport_mode_id:
            domain.append(('transport_mode_id', '=', docs.transport_mode_id.id))
        if docs.shipment_type_id:
            domain.append(('shipment_type_id', '=', docs.shipment_type_id.id))
        if docs.cargo_type_id:
            domain.append(('cargo_type_id', '=', docs.cargo_type_id.id))
        if docs.status == 'active':
            domain.append(('state', 'not in', ['cancelled', 'completed']))
        if docs.status == 'complete':
            domain.append(('state', '=', 'completed'))
        if docs.salesman_ids:
            domain.append(('sales_agent_id', 'in', docs.salesman_ids.ids))

        status = dict(docs._fields['status'].selection).get(docs.status)
        address = ''
        if docs.env.company:
            if docs.env.company.street:
                address += docs.env.company.street
            if docs.env.company.street2:
                address += (', ' if address else '') + docs.env.company.street2
            if docs.env.company.city:
                address += (', ' if address else '') + docs.env.company.city
            if docs.env.company.state_id:
                address += (', ' if address else '') + docs.env.company.state_id.name
            if docs.env.company.country_id:
                address += (', ' if address else '') + docs.env.company.country_id.name
            if docs.env.company.zip:
                address += (', ' + docs.env.company.zip)
        shipment_data = {'company_name': docs.env.company.name,
                         'company_address': address,
                         'from_date': format_date(self.env, docs.from_date),
                         'to_date': format_date(self.env, docs.to_date),
                         'status': status
                         }

        house_shipments = docs.env['freight.house.shipment'].search(domain)
        shipments = []
        total_volume = 0
        total_weight = 0
        total_teu = 0
        total_revenue = 0
        total_cost = 0
        total_profit = 0
        currency = self.env.company.currency_id

        if self.env.company.volume_uom_id:
            volume_uom_id = self.env.company.volume_uom_id
        else:
            volume_uom_id = self.env['uom.uom'].search([('name', '=', 'm³')])
        if self.env.company.weight_uom_id:
            weight_uom_id = self.env.company.weight_uom_id
        else:
            weight_uom_id = self.env['uom.uom'].search([('name', '=', 'kg')])

        for shipment in house_shipments:
            if shipment.payment_terms == 'ppx':
                payment_terms = 'PP'
            elif shipment.payment_terms == 'ccx':
                payment_terms = 'CC'
            else:
                payment_terms = ''
            cost = shipment.estimated_cost
            profit = (shipment.estimated_revenue - cost)

            if shipment.volume_unit_uom_id != self.env.company.volume_uom_id:
                volume = shipment.volume_unit_uom_id._compute_quantity(shipment.volume_unit, volume_uom_id)
            else:
                volume = shipment.volume_unit
            volume_unit_uom_id = shipment.volume_unit_uom_id and shipment.volume_unit_uom_id.name or ''
            if shipment.chargeable_uom_id != self.env.company.weight_uom_id:
                weight = shipment.chargeable_uom_id._compute_quantity(shipment.chargeable_kg, weight_uom_id)
            else:
                weight = shipment.chargeable_kg
            chargeable_uom_id = shipment.chargeable_uom_id and shipment.chargeable_uom_id.name or ''

            shipments.append({'salesman': shipment.sales_agent_id and shipment.sales_agent_id.sudo().name or '',
                              'customer': shipment.client_id and shipment.client_id.sudo().name or '',
                              'origin': shipment.origin_un_location_id and shipment.origin_un_location_id.name or '',
                              'origin_port': shipment.origin_port_un_location_id and shipment.origin_port_un_location_id.code or '',
                              'destination': shipment.destination_un_location_id and shipment.destination_un_location_id.name or '',
                              'destination_port': shipment.destination_port_un_location_id and shipment.destination_port_un_location_id.code or '',
                              'shipment_number': shipment.booking_nomination_no,
                              'payment_terms': payment_terms,
                              'volume': volume or 0.0,
                              'volume_unit_uom_id': volume_unit_uom_id,
                              'weight': weight or 0.0,
                              'chargeable_uom_id': chargeable_uom_id,
                              'teu': shipment.teu_total,
                              'revenue': shipment.estimated_revenue or 0.0,
                              'cost': cost or 0.0,
                              'profit': profit or 0.0,
                              'currency': shipment.currency_id,
                              })
            total_volume += volume
            total_weight += weight
            total_teu += shipment.teu_total
            total_revenue += shipment.estimated_revenue
            total_cost += cost
            total_profit += profit
            currency = shipment.currency_id

        data['shipment_data'] = shipment_data
        data['shipments'] = shipments
        total_volume = total_volume
        total_volume_uom = volume_uom_id.name
        total_weight = total_weight
        total_weight_uom = weight_uom_id.name
        data['totals'] = {'total_volume': total_volume or 0.0,
                          'total_volume_uom': total_volume_uom,
                          'total_weight': total_weight or 0.0,
                          'total_weight_uom': total_weight_uom,
                          'total_teu': total_teu,
                          'total_revenue': total_revenue or 0.0,
                          'total_cost': total_cost or 0.0,
                          'total_profit': total_profit or 0.0,
                          'currency': currency
                          }
        return {
            'doc_ids': docs.ids,
            'doc_model': 'shipment.profit.report',
            'data': data,
            'docs': docs,
        }
