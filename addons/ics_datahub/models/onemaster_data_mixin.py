import logging
import requests
import uuid
from odoo import models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class OnemasterDataSyncMixin(models.AbstractModel):
    _name = 'mixin.onemaster'
    _description = 'ONEMASTER Data Mixin'

    def _get_server_url(self):
        IP = self.env['instance.parameter'].sudo()
        return IP.get_param('service.onemaster.url', 'https://onemaster.searateserp.com')

    def _get_request_headers(self):
        IP = self.env['instance.parameter'].sudo()
        return {
            'Content-Type': 'application/json',
            'Instance-Client-Code': IP.get_param('instance.client_code'),
            'Instance-Client-UUID': IP.get_param('instance.uuid')
        }

    def _get_request_payload(self):
        return {}

    def _sync_onemaster_data(self, dataset_key, request_path=None, **kwargs):
        request_url = "{}/api/{}".format(self._get_server_url(), dataset_key)
        if request_path:
            request_url = "{}/{}".format(request_url, request_path)

        response = requests.post(request_url, headers=self._get_request_headers(), json={
            'jsonrpc': '2.0',
            'id': uuid.uuid4().hex,
            'params': self._get_request_payload()
        })

        if response.status_code in [200]:
            result = response.json()
            if 'error' in result:
                error_msg = "Sync Failed from ONEMASTER for {}\n{}".format(
                    self._name,
                    result.get('error').get('data').get('message')
                )
                _logger.error(error_msg)
                raise ValidationError(error_msg)
            else:
                return result.get('result')
        else:
            msg = _('Unable to process request for syncing data from ONEMASTER for {}'.format(self._name))
            _logger.error(msg)
            raise ValidationError(msg)
