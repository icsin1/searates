
from datetime import datetime
from pytz import timezone

from odoo import http
from odoo.http import request
from odoo.addons.freight_management.controllers import portal


class CustomerPortal(portal.CustomerPortal):

    @http.route()
    def track_shipment(self, tracking_number=False):
        res = super().track_shipment(tracking_number=tracking_number)
        qcontext = res.qcontext
        if not qcontext.get('master_shipment_id') and not qcontext.get('shipment_id') and tracking_number:
            service_job_id = request.env['freight.service.job'].sudo().search(
                ['|', ('booking_nomination_no', '=', tracking_number),
                 ('service_job_number', '=', tracking_number), ('event_ids', '!=', False)],
                order="id asc")
            if service_job_id:
                if request.env.user._is_public():
                    tz = service_job_id.company_id.tz
                else:
                    tz = request.env.user.tz
                dt = timezone(tz).localize(datetime.now(), is_dst=False)
                tz_str = dt.strftime('%z')
                events = (service_job_id.event_ids.with_context(tz=tz).filtered
                          (lambda ev: ev.public_visible and (ev.actual_datetime or ev.estimated_datetime)).sorted(lambda event: event.actual_datetime or event.estimated_datetime))
                active_events = events and events.filtered(
                    lambda event: (event.actual_datetime and datetime.now() <= event.actual_datetime) or (event.estimated_datetime and datetime.now() <= event.estimated_datetime)
                )
                res.qcontext.update(service_job_id=service_job_id, events=events, active_event_ids=active_events.ids, tz_str=tz_str)
        return res
