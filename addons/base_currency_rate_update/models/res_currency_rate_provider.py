# -*- coding: utf-8 -*-
import logging
import requests
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResCurrencyRateProvider(models.Model):
    _name = "res.currency.rate.provider"
    _description = "Currency Rates Provider"
    _inherit = ["mail.thread"]
    _order = "name"

    name = fields.Char(compute="_compute_name", store=True)
    service = fields.Selection(selection=[("exchange_rate_api", "Exchange Rate API")], required=True, string="Service Provider")
    currency_api_key = fields.Char(string="API Key")
    active = fields.Boolean(default=True)

    @api.depends("service")
    def _compute_name(self):
        for provider in self:
            provider.name = list(filter(lambda x: x[0] == provider.service, self._fields["service"].selection))[0][1]

    def _currency_rate_fetch_domain(self):
        return [('active', '=', True), ('fetch_exchange_rate', '=', True)]

    def _update(self):
        Currency = self.env["res.currency"].sudo()
        CurrencyRate = self.env["res.currency.rate"].sudo()
        company_ids = self.env['res.company'].sudo().search([])
        today = fields.Datetime.today().strftime('%Y-%m-%d')
        try:
            for company in company_ids:
                url = 'https://v6.exchangerate-api.com/v6/{}/latest/{}'.format(self.currency_api_key, company.currency_id.name)
                response = requests.get(url)
                data = response.json()
                if data.get('result') == 'success':
                    for currency_name, value in data.get('conversion_rates').items():
                        domain = [('name', '=', currency_name)] + self._currency_rate_fetch_domain()
                        # Search company with company specific value configured
                        currency = Currency.with_company(company).search(domain, limit=1)
                        if currency:
                            record = CurrencyRate.search([('company_id', '=', company.id), ('currency_id', '=', currency.id), ('name', '=', today)], limit=1)
                            if record:
                                record.write({'rate': value, 'provider_id': self.id})
                            else:
                                CurrencyRate.create({
                                    'company_id': company.id,
                                    'currency_id': currency.id,
                                    'name': today,
                                    'rate': value,
                                    'provider_id': self.id
                                })
                else:
                    error_msg = str(data.get('error-type')) if data.get('error-type') else _("N/A")
                    self.message_post(
                        subject=_("Currency Rate Provider Failure"),
                        body=_('Currency Rate Provider {} failed to obtain data since {} :\n{}'.format(self.name, today, error_msg))
                    )
        except BaseException as e:
            self.message_post(
                subject=_("Currency Rate Provider Failure"),
                body=_('Currency Rate Provider {} failed to obtain data since {} :\n{}'.format(self.name, today, str(e) if e else _("N/A"))))

    @api.model
    def _scheduled_update(self):
        _logger.info("Scheduled currency rates update...")
        providers = self.search([('service', '=', 'exchange_rate_api'), ('active', '=', True)], limit=1)
        if providers:
            providers._update()
            _logger.info("Currency rates updated from %s", providers.name)
        _logger.info("Scheduled currency rates process completed.")
