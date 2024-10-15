# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import request, ALLOWED_DEBUG_MODES
from odoo.tools.misc import str2bool
from odoo.addons.odoo_base import tools


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _handle_debug(self):
        if 'debug' in request.httprequest.args:
            debug_mode = []
            for debug in request.httprequest.args['debug'].split(','):
                if debug not in ALLOWED_DEBUG_MODES:
                    debug = '1' if str2bool(debug, debug) else ''
                debug_mode.append(debug)
            debug_mode = ','.join(debug_mode)

            if debug_mode != request.session.debug:
                user = request.env.user.browse(request.session.uid)
                request.session.debug = debug_mode if user.with_user(user).user_has_groups('odoo_base.group_freight_technical_support_team') else ''

    def session_info(self):
        session_info = super().session_info()
        session_info['support_url'] = 'https://searateserp.com/buy'
        version_data = tools.get_version_info()
        rpc_version_1 = {
            'application_version': version_data.get('version'),
            'application_version_info': version_data.get('version_info', []),
            'application_serie': version_data.get('serie'),
            'website': version_data.get('url'),
            'release_date': version_data.get('release_date'),
            'protocol_version': 1,
        }
        session_info['application_version'] = rpc_version_1
        return session_info
