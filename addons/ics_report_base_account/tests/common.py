from odoo.addons.ics_account.tests.common import ICSAccountTestCommon


class AccountReportTestCommon(ICSAccountTestCommon):

    _web_report_ref = None

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super(AccountReportTestCommon, cls).setUpClass(chart_template_ref=chart_template_ref or 'l10n_generic_coa.configurable_chart_template')
        cls.web_report = cls.env.ref(cls._web_report_ref, False) if cls._web_report_ref else None
        cls.setup_report_data()

    @classmethod
    def setup_report_data(cls):
        cls.report_options = cls.web_report and cls.web_report._get_options({}) or {}
        cls.report_kwargs = {}

    def set_report_options(self, options, **kwargs):
        self.report_options = self.web_report and self.web_report._get_options(options) or {}
        self.report_kwargs = kwargs

    def get_report_data(self, context={}, **kwargs):
        return self.web_report.with_context(**context).with_company(self.company_data['company']).get_web_report(self.report_options, **self.report_kwargs)

    def assertSectionValueEqual(self, section, value_key, value_to_check, message=None, **kwargs):
        value_key_name = f'{value_key}_original'
        section_value = section.get('values', {}).get('main_group').get(value_key_name, False)
        self.assertEqual(section_value, value_to_check, message or '')
