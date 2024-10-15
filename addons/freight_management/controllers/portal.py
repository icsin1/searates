
from datetime import datetime
from pytz import timezone

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):

    @http.route(['/track/shipment', '/track/shipment/<string:tracking_number>'], type="http", auth="public", website=True, methods=['GET'], csrf=False)
    def track_shipment(self, tracking_number=False):
        values = {
            'tracking_number': tracking_number,
            'no_breadcrumbs': True,
        }
        if tracking_number:
            shipment_id = request.env['freight.house.shipment'].sudo().search(
                ['|', ('hbl_number', '=', tracking_number), ('name', '=', tracking_number), ('event_ids', '!=', False)],
                order="id asc")

            master_shipment_id = request.env['freight.master.shipment'].sudo().search(
                ['|', ('carrier_booking_reference_number', '=', tracking_number), ('name', '=', tracking_number), ('event_ids', '!=', False)],
                order="id asc")

            if shipment_id:
                if request.env.user._is_public():
                    tz = shipment_id.company_id.tz
                else:
                    tz = request.env.user.tz or 'UTC'
                dt = timezone(tz).localize(datetime.now(), is_dst=False)
                tz_str = dt.strftime('%z')
                events = (shipment_id.event_ids.with_context(tz=tz).filtered
                          (lambda ev: ev.public_visible and (ev.actual_datetime or ev.estimated_datetime)).sorted(lambda event: event.actual_datetime or event.estimated_datetime))
                active_events = events and events.filtered(
                    lambda event: (event.actual_datetime and datetime.now() <= event.actual_datetime)
                    or (event.estimated_datetime and datetime.now() <= event.estimated_datetime)
                )
                values.update(shipment_id=shipment_id, events=events, active_event_ids=active_events.ids, tz_str=tz_str)

            if master_shipment_id:
                if request.env.user._is_public():
                    tz = master_shipment_id.company_id.tz
                else:
                    tz = request.env.user.tz or 'UTC'
                dt = timezone(tz).localize(datetime.now(), is_dst=False)
                tz_str = dt.strftime('%z')
                events = (master_shipment_id.event_ids.with_context(tz=tz).filtered
                          (lambda ev: ev.public_visible and (ev.actual_datetime or ev.estimated_datetime)).sorted(lambda event: event.actual_datetime or event.estimated_datetime))
                active_events = events and events.filtered(
                    lambda event: (event.actual_datetime and datetime.now() <= event.actual_datetime)
                    or (event.estimated_datetime and datetime.now() <= event.estimated_datetime)
                )
                values.update(master_shipment_id=master_shipment_id, events=events, active_event_ids=active_events.ids, tz_str=tz_str)
        return request.render('freight_management.shipment_tracking_portal_template', values)
