import uuid
import requests
import logging
import traceback
from odoo import exceptions, _

_logger = logging.getLogger(__name__)


def service_jsonrpc(env, url, method='call', http_method='POST', params={}, headers=None, timeout=15):
    """
    Calls the provided JSON-RPC endpoint, unwraps the result and
    returns JSON-RPC errors as exceptions.
    """
    payload = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': uuid.uuid4().hex,
    }
    IP = env['instance.parameter'].sudo()
    request_headers = {
        'Content-Type': 'application/json',
        'Instance-Client-Code': IP.get_param('instance.client_code'),
        'Instance-Client-UUID': IP.get_param('instance.uuid'),
        **(headers or {})
    }

    _logger.info('service jsonrpc %s', url)

    try:
        req = requests.request(http_method, url, json=payload, timeout=timeout, headers=request_headers)
        req.raise_for_status()

        if http_method == 'GET' and 'application/json' not in req.headers.get('Content-Type'):
            return req
        response = req.json()
        if 'error' in response:
            name = response['error']['data'].get('name').rpartition('.')[-1]
            message = response['error']['data'].get('message')
            if name == 'InsufficientCreditError':
                e_class = InsufficientCreditError
            elif name == 'AccessError':
                e_class = exceptions.AccessError
            elif name == 'UserError':
                e_class = exceptions.UserError
            else:
                raise requests.exceptions.ConnectionError()
            e = e_class(message)
            e.data = response['error']['data']
            raise e
        return response.get('result')
    except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.MissingSchema, requests.exceptions.Timeout, requests.exceptions.HTTPError):
        traceback.print_exc()
        raise exceptions.AccessError(
            _('The url that this service requested returned an error. Please contact the author of the app. The url it tried to contact was %s', url)
        )


class InsufficientCreditError(Exception):
    pass
