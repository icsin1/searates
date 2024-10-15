# -*- coding: utf-8 -*-

from odoo import models


class VatReportHandler(models.AbstractModel):
    _name = 'vat.report.handler'
    _description = 'Tanzania Vat Report'
    _inherit = ['mixin.report.handler']

    def _get_section_lines(self):
        return {
            'Supplies Of Goods and Services': {
                '1. Standard Rated Sales': {'base': ['+BASE VAT 18%', '-BASE VAT 18%'], 'vat': ['+VAT 18%', '-VAT 18%'], 'level': 3},
                '2. Special Relief Sales': {'base': [], 'vat': [], 'level': 3},
                '3. Zero Rated Sales (Local)': {'base': ['+BASE VAT 0% LOCAL', '-BASE VAT 0% LOCAL'], 'vat': [], 'level': 3},
                '4. Zero Rated Sales - Export (Zero rated Supplies)': {'base': ['+BASE VAT 0% EXPORT', '-BASE VAT 0% EXPORT'], 'vat': [], 'level': 3},
                '5. Exempt Sales - Local': {'base': ['+BASE VAT EXEMPT', '-BASE VAT EXEMPT'], 'vat': [], 'level': 3},
                'Total (Sum of row 1 to 5)': {
                    'base': ['+BASE VAT 18%', '+BASE VAT 0% LOCAL', '+BASE VAT 0% EXPORT', '+BASE VAT EXEMPT',
                             '-BASE VAT 18%', '-BASE VAT 0% LOCAL', '-BASE VAT 0% EXPORT', '-BASE VAT EXEMPT'],
                    'vat': ['+VAT 18%', '-VAT 18%'],
                    'level': 2
                },
            },
            'Purchases Of Goods and Services': {
                '1. Standard Rated Purchase - Local (Transfer total from Local receipt & GePG receipts)': {
                    'base': ['-BASE VAT 18% LOCAL', '+BASE VAT 18% LOCAL'],
                    'vat': ['-VAT 18% LOCAL', '+VAT 18% LOCAL'],
                    'level': 3
                },
                '2. Standard Rated Purchases - Imports (Transfer total from Wharfage and Imports)': {
                    'base': ['-BASE VAT 18% IMPORT', '+BASE VAT 18% IMPORT'],
                    'vat': ['-VAT 18% IMPORT', '+VAT 18% IMPORT'],
                    'level': 3
                },
                '3. Exempt Purchases - Local': {'base': ['-BASE VAT EXEMPT LOCAL', '+BASE VAT EXEMPT LOCAL'], 'vat': [], 'level': 3},
                '4. Exempt Purchases - Imports': {'base': ['-BASE VAT EXEMPT IMPORT', '+BASE VAT EXEMPT IMPORT'], 'vat': [], 'level': 3},
                '5. Non-creditable purchases - Local': {'base': [], 'vat': [], 'level': 3},
                '6. Non-creditable purchases - Imports': {'base': [], 'vat': [], 'level': 3},
                'Total (Sum of row 1 to 6)': {
                    'base': ['-BASE VAT 18% LOCAL', '-BASE VAT 18% IMPORT', '-BASE VAT EXEMPT LOCAL', '-BASE VAT EXEMPT IMPORT',
                             '+BASE VAT 18% LOCAL', '+BASE VAT 18% IMPORT', '+BASE VAT EXEMPT LOCAL', '+BASE VAT EXEMPT IMPORT'],
                    'vat': ['-VAT 18% LOCAL', '-VAT 18% IMPORT', '+VAT 18% LOCAL', '+VAT 18% IMPORT'],
                    'level': 2
                },
            },
            'Computation of Tax': {
                '1. Output Tax for the Period (Transfer from Supplies Of Goods and Services)': {'base': [], 'vat': ['+VAT 18%', '-VAT 18%'], 'level': 3},
                '2. Input Tax for the period (Transfer from Purchases Of Goods and Services)': {'base': [], 'vat': ['-VAT 18% LOCAL', '-VAT 18% IMPORT', '+VAT 18% LOCAL', '+VAT 18% IMPORT'], 'level': 3},
                '3. Total VAT Payable/(Refundable)  - (Row 1 minus 2)': {
                    'base': [],
                    'vat': ['+VAT 18%', '-VAT 18% LOCAL', '-VAT 18% IMPORT', '-VAT 18%', '+VAT 18% LOCAL', '+VAT 18% IMPORT'],
                    'level': 2
                },
                '4. Vat Credit Brought Forward from previous period': {
                    'base': [],
                    'vat': [],
                    'level': 3
                },
                'Total VAT Due/(Carried Forward) - (row 3 minus 4)': {
                    'base': [],
                    'vat': ['+VAT 18%', '-VAT 18% LOCAL', '-VAT 18% IMPORT', '-VAT 18%', '+VAT 18% LOCAL', '+VAT 18% IMPORT'],
                    'level': 2
                },
            },
        }

    def _calculate_amount_without_tax(self, DataModel, report_group, child_sec):
        return DataModel.search(report_group.get('__domain', []) + [('tax_tag_ids.name', 'in', child_sec.get('base'))]).mapped('balance')

    def _calculate_vat_charged(self, DataModel, report_group, child_sec):
        return DataModel.search(report_group.get('__domain', []) + [('tax_tag_ids.name', 'in', child_sec.get('vat'))]).mapped('balance')

    def _get_sections(self, report, options, **kwargs):
        sections = []
        DataModel = self.env[report.model_name]

        report_groups = options.get('report_header_groups', {})

        for report_group_key, report_group in report_groups.items():
            section_lines = self._get_section_lines()

            for key, values in section_lines.items():
                values = self._generate_values(report, {
                    'sale_parent_section': key,
                    'sale_parent_section_base': 0.0,
                    'sale_parent_section_vat': 0.0
                })
                sections.append(self._generate_section({
                    'action': False,
                    'title': key,
                    'level': 0,
                    'values': {report_group_key: values}
                }))
                for child_line, child_sec in section_lines[key].items():
                    amount_without_tax = self._calculate_amount_without_tax(DataModel, report_group, child_sec)
                    vat_charged = self._calculate_vat_charged(DataModel, report_group, child_sec)
                    if key == 'Purchases Of Goods and Services' or child_line == '2. Input Tax for the period (Transfer from Purchases Of Goods and Services)':
                        child_sec['total_vat_amount'] = sum(vat_charged)
                    else:
                        child_sec['total_vat_amount'] = -sum(vat_charged)

                    if child_line == '3. Total VAT Payable/(Refundable)  - (Row 1 minus 2)':
                        section_line_33 = section_lines[key].get('1. Output Tax for the Period (Transfer from Supplies Of Goods and Services)')
                        section_line_34 = section_lines[key].get('2. Input Tax for the period (Transfer from Purchases Of Goods and Services)')
                        child_sec['total_vat_amount'] = section_line_33.get('total_vat_amount', 0) - section_line_34.get('total_vat_amount', 0)

                    if child_line == 'Total VAT Due/(Carried Forward) - (row 3 minus 4)':
                        section_line_35 = section_lines[key].get('3. Total VAT Payable/(Refundable)  - (Row 1 minus 2)')
                        section_line_36 = section_lines[key].get('4. Vat Credit Brought Forward from previous period')
                        child_sec['total_vat_amount'] = section_line_35.get('total_vat_amount', 0) - section_line_36.get('total_vat_amount', 0)

                    report_values = self._generate_values(report, {
                        'sale_parent_section': child_line,
                        'sale_parent_section_base': sum(amount_without_tax) if key == 'Purchases Of Goods and Services' else -sum(amount_without_tax),
                        'sale_parent_section_vat': child_sec.get('total_vat_amount', 0)
                    })
                    sections.append(self._generate_section({
                        'action': False,
                        'title': child_line,
                        'level': child_sec.get('level', 0),
                        'values': {report_group_key: report_values}
                    }))
        return sections

    def _process_values(self, move, values, options, **kwargs):
        return values

    def _get_action(self, move):
        return {}

    def _get_objs_for_report(self, docids, data):
        # OVERRIDING EXCEL Object browser
        return self
