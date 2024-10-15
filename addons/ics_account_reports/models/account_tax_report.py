import ast
from odoo import models, _
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression
from .variable_object import VariableObject


class AccountTaxReport(models.Model):
    _name = 'account.html.tax.report'
    _inherit = 'account.finance.report.mixin'
    _description = 'Account Tax Report'

    def get_title(self):
        return _('Tax Report')

    def get_account_report_data(self, options, **kwargs):
        self.has_date_range = True
        self.is_tax_report = True
        values = super().get_account_report_data(options, **kwargs)
        values['sections'] = self.get_sorted(options, self._get_sections(options, **kwargs))
        return values

    def _get_sections(self, options, **kwargs):
        report = options.get('active_tax_report', 0)
        headers = options.get("headers")
        sections = []
        if not report:
            return sections
        report = self.env['account.tax.report'].sudo().browse(report.get('id'))
        level = 1
        variables = {headers[0]: VariableObject()}
        for root_line in report.root_line_ids:
            group_by = ''
            root_line_key = root_line.code or f'RL_{root_line.id}'
            children = self._get_tax_report_child_lines(root_line, root_line.children_line_ids, options, level=level, variables=variables, **kwargs)
            total_amount = 0
            if not root_line.formula and not root_line.tag_name:
                computed_child = root_line.children_line_ids.filtered(lambda c: not c.code and not c.tag_name and c.formula)
                if computed_child:
                    total_amount = sum([child.get('values')[headers[0]][0] for child in children if child.get('id') in computed_child.ids])
            elif root_line.tag_name:
                # Root line tags
                root_records = self._get_tax_report_child_lines(root_line, root_line, options, level=level, variables=variables, **kwargs)
                total_amount = sum([child.get('values')[headers[0]][0] for child in root_records])
                group_by = 'move_id'
            else:
                total_amount = self._compute_value_from_dict(root_line, variables[headers[0]])

            variables[headers[0]][root_line_key] = total_amount
            row_class = ''
            if not children and not root_line.tag_name and root_line.formula:
                row_class = 'bg-200'
            sections.append({
                'id': root_line.id,
                'title': root_line.name,
                'code': root_line.code or f'RL_{root_line.id}',
                'level': level,
                'row_class': row_class,
                'group_by': group_by,
                'values': {headers[0]: (total_amount, self._format_currency(total_amount))},
                'children': children,
                'parent_id': False,
                'is_expandable': True
            })
        return sections

    def _get_tax_report_child_lines(self, root_line, child_lines, options, level, variables, **kwargs):
        headers = options.get("headers")
        sections = []
        child_level = level + 1
        for child_line in child_lines:
            line_key = child_line.code or f'RCL_{root_line.id}'
            children = child_line.children_line_ids
            record_count = self._get_record_count(child_line, options, **kwargs) if not children and child_line.tag_name else 0
            row_class = ''
            if record_count:
                row_class += ' text-info'
            if child_line.tag_name or child_line.code:
                row_class += ' font-weight-normal'
            children = self._get_tax_report_child_lines(child_line, children, options, level=child_level, variables=variables, **kwargs)

            if not child_line.tag_name and not child_line.formula and children:
                computed_child = child_line.children_line_ids.filtered(lambda c: not c.code and not c.tag_name and c.formula)
                move_line_amount = sum([child.get('values')[headers[0]][0] for child in children if child.get('id') in computed_child.ids])
            elif child_line.formula:
                move_line_amount = self._compute_value_from_dict(child_line, variables[headers[0]])
            else:
                move_line_amount = self._get_move_line_amount(child_line, options, **kwargs)

            # Updating amount for key
            variables[headers[0]][line_key] = move_line_amount
            sections.append({
                'id': child_line.id,
                'title': child_line.name,
                'code': line_key,
                'level': child_level,
                'row_class': row_class or 'font-weight-bold',
                'group_by': 'move_id' if record_count else '',
                'values': {headers[0]: (move_line_amount, self._format_currency(move_line_amount))},
                'parent_id': root_line.id,
                'children': children,
                'is_expandable': bool(children)
            })
        return sections

    def _get_record_line_domain(self, tax_report_line, options, **kwargs):
        tag_ids = tax_report_line.tag_ids
        domain = self._generate_domain(options, **kwargs)
        tag_grid_domain = tag_ids and [('tax_tag_ids', 'in', tag_ids.ids)] or []
        additional_domain = tax_report_line.include_additional_data_domain and ast.literal_eval(tax_report_line.additional_data_domain) or []

        # Final domain
        domain = expression.AND([domain, expression.OR([tag_grid_domain, additional_domain])])
        return domain

    def _get_record_count(self, child_line, options, **kwargs):
        domain = self._get_record_line_domain(child_line, options, **kwargs)
        return self._get_account_moves(domain, count=True)

    def _get_move_line_amount(self, tax_line, options, **kwargs):
        domain = self._get_record_line_domain(tax_line, options, **kwargs)
        move_lines = self._get_account_moves(domain)
        tag_amount = 0
        for line in move_lines:
            tag_amount += self._get_tag_amount_from_line(tax_line, line)
        return tag_amount

    def _compute_value_from_dict(self, line, variables):
        amount = 0
        if line.formula:
            formula = "result = {}".format(line.formula)
            safe_eval(formula, variables, mode='exec', nocopy=True)
            amount = variables.result

        # Removing builtins variables for clean dict
        if '__builtins__' in variables:
            del variables['__builtins__']
        return amount

    def _get_tag_amount_from_line(self, tax_report_line, line):
        tag_amount = 0
        if line.tax_tag_ids:
            for tag in line.tax_tag_ids.filtered(lambda k: k in tax_report_line.tag_ids):
                tag_amount += (line.tax_tag_invert and -1 or 1) * (tag.tax_negate and -1 or 1) * line.balance
        else:
            # In case of no tax grid defined but move line is related to sale/purchase (or refunds)
            move_type_mul = {
                'in_invoice': 1,
                'in_refund': -1,
                'out_invoice': 1,
                'out_refund': -1
            }
            tag_amount = move_type_mul.get(line.move_id.move_type, -1) * abs(line.balance)
        return tag_amount

    def get_account_report_section_data(self, parent, options, **kwargs):
        headers = options.get("headers")
        report_line = self.env['account.tax.report.line'].sudo().browse(parent.get('id'))
        tax_domain = self._get_record_line_domain(report_line, options, **kwargs)
        data_domain = tax_domain + self._generate_domain(options, **kwargs)
        records = []
        for line in self._get_account_moves(data_domain):
            tag_amount = self._get_tag_amount_from_line(report_line, line)
            records += [{
                'id': line.id,
                'title': f'{line.name} ({line.move_id.name})',
                'code': line.id,
                'level': 3,
                'row_class': 'font-weight-normal',
                'move_id': line.move_id.id,
                'group_by': False,
                'values': {
                    headers[0]: (tag_amount, self._format_currency(tag_amount))
                }
            }]
        return records
