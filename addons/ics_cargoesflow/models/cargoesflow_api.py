import requests
import json
from odoo.exceptions import ValidationError


class CargoesflowAPI:

    def __init__(self, env):
        self.env = env
        self._set_parameters()

    def _set_parameters(self):
        ins_parameters = self.env['instance.parameter'].sudo()
        self.base_url = ins_parameters.get_param('service.cargoesflow.base_url', '')
        self.api_key = ins_parameters.get_param('service.cargoesflow.api_key', '')
        self.org_token = ins_parameters.get_param('service.cargoesflow.org_token', '')

    def _get_headers(self):
        return {
            'X-DPW-ApiKey': self.api_key,
            'X-DPW-Org-Token': self.org_token,
        }

    def _rpc(self, path, payload, headers=None):
        headers = {
            **self._get_headers(),
            **(headers or {})
        }

        url = "{}{}".format(self.base_url, path)
        return requests.post(url, headers=headers, data=json.dumps(payload))

    def _create_shipment(self, shipment_details):
        payload = shipment_details
        response = self._rpc('/createShipments', payload=payload)
        if response.status_code == 200:
            return response.json().get('result') == 'SUCCESS'
        else:
            raise ValidationError(response.json().get('message'))

    def _update_shipment(self, cargoesflow_shipment_number, shipment_details):
        """ Parked for future usage """
        pass

    def _get_shipment_detail(self, reference_number, shipment_type='INTERMODAL_SHIPMENT'):
        url = '{}/shipments'.format(self.base_url)

        params = {
            'shipmentType': shipment_type,
            'mblNumber' if shipment_type == 'INTERMODAL_SHIPMENT' else 'awbNumber': reference_number
        }
        response = requests.get(url, params, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        return []

    def _get_tracking_url(self, payload):
        response = self._rpc('/generateSharingUrl', payload)
        if response.status_code == 200:
            return response.json().get('url')
        else:
            raise ValidationError(response.json().get('message'))

    def _get_shipment_tracking_url(self, reference_number, mode_type='sea'):
        return self._get_tracking_url({
            'mblNumber' if mode_type == 'sea' else 'awbNumber': reference_number
        })

    def _get_container_tracking_url(self, container_number):
        return self._get_tracking_url({'containerNumber': container_number})
