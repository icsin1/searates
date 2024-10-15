# -*- coding: utf-8 -*-

import base64
import json

from odoo import http
from odoo.http import request


class StimulsoftNodeJSDataController(http.Controller):

    @http.route(['/stimulsoft-nodejs/get-data'], type='json', methods=['POST'], auth="user")
    def stimulsoft_data_request(self, **kwargs):
        template_model, template_id = kwargs.get('template_id', '').split(',')
        record_model, record_id = kwargs.get('record_id', '').split(',')

        report_template_obj = request.env[template_model].sudo().browse(int(template_id))

        report_action = False
        if report_template_obj._name == 'stimulsoft.mrt.report.product':
            report_action = report_template_obj.report_id.report_id
        else:
            report_action = report_template_obj.report_id

        record = request.env[record_model].sudo().browse(int(record_id))

        template_data = json.loads(base64.b64decode(report_template_obj.mrt_file).decode('utf-8'))
        record_json = report_action._record_to_json(record, json_spec=report_template_obj.json_spec_id)

        response = {
            'gc_si_key': request.env['instance.parameter'].sudo().get_param('gc.stimulsoft.key', ''),
            'template': template_data,
            'record': record_json
        }
        return response
