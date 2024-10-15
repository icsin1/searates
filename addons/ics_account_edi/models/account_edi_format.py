# -*- coding: utf-8 -*-

import json

from odoo import models
from odoo.addons.ics_service_manager import jsonrpc


DEFAULT_SERVICE_URL = 'https://service-einv.searateserp.com'


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    def _is_enabled_by_default_on_journal(self, journal):
        self.ensure_one()
        return super()._is_enabled_by_default_on_journal(journal)

    def _is_required_for_invoice(self, invoice):
        self.ensure_one()
        return super()._is_required_for_invoice(invoice)

    def _needs_web_services(self):
        self.ensure_one()
        return self.code == "edi_sr_env" or super()._needs_web_services()

    def _get_invoice_edi_content(self, move):
        if self.code != "edi_sr_env":
            return super()._get_invoice_edi_content(move)
        json_dump = json.dumps(self._generate_json_payload(move))
        return json_dump.encode()

    def _generate_json_payload(self, move):
        json_schema = self.env.ref('ics_account_edi.einvoice_json_specification').sudo()
        return json_schema._to_dict(move)

    def _post_invoice_status_check(self, documents, invoices):
        for edi_document in documents:
            for company in invoices.mapped('company_id'):
                company_invoices = invoices.filtered(lambda inv: inv.company_id == company and inv.einvoice_request_uuid)
                response = self._edi_call_status_api(company, company_invoices.mapped('einvoice_request_uuid'))
                for invoice in company_invoices:
                    request_status = response.get('data', {}).get(invoice.einvoice_request_uuid)
                    attachment = self.env["ir.attachment"].create({
                        "name": "%s_einvoice.json" % (invoices.name.replace("/", "_")),
                        "raw": json.dumps(request_status.get('response')).encode(),
                        "res_model": "account.move",
                        "res_id": invoices.id,
                        "mimetype": "application/json",
                    })
                    edi_document.attachment_id = attachment
                    if request_status:
                        invoice_vals = {
                            'einvoice_request_status': request_status.get('status'),
                            'einvoice_request_status_help': request_status.get('status_help'),
                            'einvoice_request_fail_reason': json.dumps(request_status.get('fail_reason'))
                        }
                        if request_status.get('status') == 'failed':
                            edi_document.write({
                                "error": request_status.get('fail_reason', {}).get(invoice.name, False),
                                "blocking_level": "error",
                                "state": "fail"
                            })
                        invoice.write(invoice_vals)
                        # Update IRN to Invoice
                        for invoice in invoices:
                            response_json = invoice._get_edi_response_json()
                            if response_json and response_json.get('irn'):
                                invoice.write({'einvoice_irn': response_json.get('irn')})

    def _post_invoice_edi(self, invoices):
        if self.code != "edi_sr_env":
            return super()._post_invoice_edi(invoices)
        response = {}
        res = {}
        json_payload = self._generate_json_payload(invoices)
        response = self._edi_call_api(invoices.company_id, json_payload)

        if response.get("error"):
            # error_code = response.get('error_code')
            # Invalid Token Passed
            # if error_code == -32001:
            res[invoices] = {
                "success": False,
                "error": response.get('error'),
                "blocking_level": "error",
            }

        if not response.get('error'):
            # BY Passing for now
            invoice_response = response.get('data', {}).get(invoices.name, {})
            json_dump = json.dumps(invoice_response)
            attachment = self.env["ir.attachment"].create({
                "name": "%s_einvoice.json" % (invoices.name.replace("/", "_")),
                "raw": json_dump.encode(),
                "res_model": "account.move",
                "res_id": invoices.id,
                "mimetype": "application/json",
            })
            is_failed = invoice_response.get('status') == 'failed'
            res[invoices] = {"success": not is_failed, 'error': invoice_response.get('status_help', ''), 'blocking_level': 'error' if is_failed else '', "attachment": attachment}
            invoices.write({
                'einvoice_request_uuid': invoice_response.get('request_uuid'),
                'einvoice_request_status': invoice_response.get('status'),
                'einvoice_request_status_help': invoice_response.get('status_help'),
                'einvoice_request_fail_reason': json.dumps(invoice_response.get('fail_reason')),
            })
        return res

    def _cancel_invoice_edi(self, invoices):
        if self.code != "edi_sr_env":
            return super()._cancel_invoice_edi(invoices)
        res = {}
        for invoice in invoices:
            response_json = invoice._get_edi_response_json()
            cancel_json = {
                'invoice_number': invoice.name,
                'signature': response_json.get('irn'),
                'cancel_reason': invoice.einvoice_cancel_reason,
                'cancel_remarks': invoice.einvoice_cancel_remarks or '',
            }
            response = self._edi_call_cancel_api(invoice.company_id, cancel_json)

            if response.get("error"):
                # error_code = response.get('error_code')
                # Invalid Token Passed
                # if error_code == -32001:
                res[invoices] = {
                    "success": False,
                    "error": response.get('error'),
                    "blocking_level": "error",
                }

            if not response.get("error"):
                invoice_response = response.get('data', {}).get(invoices.name, {})
                json_dump = json.dumps(invoice_response)
                json_name = "%s_cancel_einvoice.json" % (invoice.name.replace("/", "_"))
                attachment = self.env["ir.attachment"].create({
                    "name": json_name,
                    "raw": json_dump.encode(),
                    "res_model": "account.move",
                    "res_id": invoice.id,
                    "mimetype": "application/json",
                })
                res[invoice] = {"success": True, "attachment": attachment}
                invoice_response = response.get('data', {}).get(invoices.name, {})
                inv_vals = {
                    'einvoice_request_uuid': invoice_response.get('request_uuid'),
                    'einvoice_request_status': 'Cancelled' if invoice_response.get('status') == 'done' else 'cancel-inprogress',
                    'einvoice_request_status_help': invoice_response.get('status_help'),
                    'einvoice_request_fail_reason': json.dumps(invoice_response.get('fail_reason')),
                }
                invoice.write(inv_vals)
        return res

    def _get_edi_headers(self, company):
        return {
            'Authorization': company.ics_edi_token
        }

    def _edi_call_api(self, company, payload):
        IP = self.env['instance.parameter'].sudo()
        einvoice_url = IP.get_param('hub.einvoice.url', DEFAULT_SERVICE_URL)
        params = {
            'invoices': [payload]
        }
        headers = self._get_edi_headers(company)
        endpoint = "%s%s" % (einvoice_url, '/api/e-invoice/%s/create' % (company.country_id.code))
        return jsonrpc(self.env, endpoint, params=params, headers=headers, timeout=25)

    def _edi_call_status_api(self, company, request_uuids):
        IP = self.env['instance.parameter'].sudo()
        einvoice_url = IP.get_param('hub.einvoice.url', DEFAULT_SERVICE_URL)
        params = {
            'request_uuids': request_uuids
        }
        headers = self._get_edi_headers(company)
        endpoint = "%s%s" % (einvoice_url, '/api/e-invoice/status')
        return jsonrpc(self.env, endpoint, params=params, headers=headers, timeout=25)

    def _edi_call_cancel_api(self, company, payload):
        IP = self.env['instance.parameter'].sudo()
        einvoice_url = IP.get_param('hub.einvoice.url', DEFAULT_SERVICE_URL)
        params = {
            'invoices': [payload]
        }
        headers = self._get_edi_headers(company)
        endpoint = "%s%s" % (einvoice_url, '/api/e-invoice/%s/cancel' % (company.country_id.code))
        return jsonrpc(self.env, endpoint, params=params, headers=headers, timeout=25)

    def _check_move_configuration(self, move):
        return super()._check_move_configuration(move)
