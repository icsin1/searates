import ast
import logging
import traceback
from odoo import models, fields, _
from odoo.tools.safe_eval import safe_eval
from odoo.addons.web.controllers.main import clean_action

_logger = logging.getLogger(__name__)


class WebReportLine(models.Model):
    _name = 'web.report.line'
    _inherit = 'mixin.base.report.line'
    _description = 'Web Report Line'

    web_report_id = fields.Many2one('web.report', required=True, ondelete='cascade')
    model_id = fields.Many2one('ir.model', related='web_report_id.model_id', store=True)
    action_field_id = fields.Many2one('ir.model.fields', domain="[('model_id', '=', model_id), ('ttype', 'in', ['many2one', 'many2many', 'one2many'])]")
    model_name = fields.Char(related='model_id.model', store=True)
    expression_ids = fields.One2many('web.report.expression', 'web_report_line_id', string='Expressions')

    parent_id = fields.Many2one('web.report.line', string='Parent')
    child_ids = fields.One2many('web.report.line', 'parent_id', string='Child')

    strict_on_date_range = fields.Boolean(default=True)

    def _get_section_data(self, options, parent_section=None, **kwargs):
        self.ensure_one()
        sections = []
        section_domain = []

        if parent_section:
            report_groups = options.get('report_header_groups', {})
            section_domain = parent_section and parent_section.get('_filter_domain', []) or []

            # adding group filter date range so that data will be loaded on given period only
            group_filters = list(report_groups.values())

            group_date_from = group_filters[0].get('group_period', {}).get('date_from')
            group_date_to = group_filters[-1].get('group_period', {}).get('date_to')
            date_field = self.web_report_id.date_field.name
            section_domain += [(date_field, '<=', group_date_to)]
            if options.get('filter_date_options', {}).get('mode') == 'range':
                section_domain += [(date_field, '>=', group_date_from)]

            parent_title = parent_section and parent_section.get('title') or None
            if parent_title:
                kwargs.update({'title': parent_title, 'current_group_by': parent_section.get('current_group_by')})

        if self.group_by_fields and not parent_section:
            group_by_fields = self.group_by_fields.split(',')
            group_by = group_by_fields[0]
            sub_groups = ','.join(list(set(group_by_fields) - set([group_by])))
            sections += self._get_grouping_data(group_by.strip(), sub_groups, options, domain=section_domain, **kwargs)
            report_handler = self.web_report_id._get_report_handler()
            if report_handler is not None:
                sections = report_handler._post_process_sections(
                    self.web_report_id,
                    self,
                    sections,
                    options,
                    domain=section_domain,
                    current_group_by=group_by.strip(),
                    **kwargs
                )
        elif parent_section:
            group_by_fields = list(set(self.group_by_fields.split(',')) - set([parent_section.get('code')]))
            group_by = group_by_fields[0]
            sections += self._get_grouping_data(group_by.strip(), ','.join(list(set(group_by_fields) - set([group_by]))), options, domain=section_domain, **kwargs)

        # Group Header
        if (self.group_total or not self.group_by_fields):
            parent_group_by = parent_section and parent_section.get('current_group_by', False)
            group_total = self._get_grouping_data(parent_group_by, [], options, domain=section_domain, group_total=True, **kwargs)

            if group_total and not parent_section and not self.group_by_fields:
                sections = [{
                    **group_total[0],
                    'level': self.hierarchy_level + kwargs.get('level', 1),
                    'action': self._get_action() if not self.action_field_id else False,
                    'foldable': False
                }] + sections

        if self.group_total and group_total:
            # Group total at bottom
            sections += [{
                **group_total[0],
                'title': _('Total {}'.format(parent_section and parent_section.get('title') or group_total[0].get('title'))),
                'level': self.hierarchy_level + kwargs.get('level', 1),
                'row_class': 'ics_group_total',
                'action': self._get_action() if not self.action_field_id else False,
                'foldable': False
            }]
        return sections

    def _get_group_data(self, data_fields, domain, group_by, sub_group_by, options, **kwargs):
        self.ensure_one()
        if group_by and group_by == 'id':
            if kwargs.get('current_group_by'):
                data_fields += [kwargs.get('current_group_by')]
            read_fields = ['display_name', 'name']
            if self.action_field_id:
                read_fields.append(self.action_field_id.name)

            def _parse_res_id(group):
                res_id = group.get('id')
                if self.action_field_id:
                    res_id = group.get(self.action_field_id.name)
                    if isinstance(res_id, tuple):
                        res_id = res_id[0]
                    else:
                        # setting record id
                        res_id = group.get('id')
                return res_id

            groups = self.env[self.web_report_id.model_name].sudo().search(domain, order=kwargs.get('order_by')).read(read_fields + data_fields)
            groups = [{**group, '__domain': [('id', '=', group.get('id'))], 'res_id': _parse_res_id(group)} for group in groups]
            sub_group_by = False
        else:
            non_aggregated_fields = set(self.expression_ids.filtered(lambda exp: exp.computation_engine == 'field' and not exp.allow_aggregate).mapped('name'))
            group_by_fields = list(set(data_fields) - non_aggregated_fields)
            groups = self.env[self.web_report_id.model_name].sudo().read_group(domain, group_by_fields or ['id'], [group_by] if group_by else [], orderby=kwargs.get('order_by'))
            # Returning empty as there is nothing inside
            if groups and len(groups) <= 1 and (groups[0].get('__count', 0) == 0) and not group_by:
                return [], sub_group_by
        return groups, sub_group_by

    def _get_handler_sections(self, report, handler, options, **kwargs):
        records = []
        data_fields = self.expression_ids.filtered(lambda exp: exp.computation_engine == 'field').mapped('name')
        handler_methods = list(set(self.expression_ids.filtered(lambda exp: exp.formula_expression.startswith('_report_handler_')).mapped('formula_expression')))

        group_by_fields = self.group_by_fields.split(',')
        group_by = group_by_fields[0]
        sub_groups = ','.join(list(set(group_by_fields) - set([group_by])))

        for handler_method in handler_methods:
            if hasattr(handler, handler_method):
                records += getattr(handler, handler_method)(report, self, data_fields, options, current_group_by=group_by, sub_group_by=sub_groups, **kwargs)
        return records

    def _groups_to_sections(self, groups, group_by, options, sub_group_by=None, extra_params={}, **kwargs):
        records = []
        data_fields = self.expression_ids.filtered(lambda exp: exp.computation_engine == 'field').mapped('name')
        report_groups = options.get('report_header_groups', {})

        for idx, group in enumerate(groups):
            report_group_values = {}
            for report_group_key, report_group in report_groups.items():
                variables = {
                    **group,
                    **{field_name: group and group.get(field_name) or False for field_name in data_fields}
                }
                report_group_domain = report_group.get('__domain', []) + group.get('__domain', [])
                group_value = {}

                if self.web_report_id.enable_report_handler_code:
                    handler_code_result = self.web_report_id._compute_handler_code(dict(
                        web_report=self.web_report_id,
                        web_report_line=self,
                        record=group,
                        record_domain=report_group_domain,
                        options=options,
                        group_by=group_by,
                        sub_group_by=sub_group_by,
                        **kwargs
                    )) or {}
                    variables.update(handler_code_result)

                for expression in self.expression_ids:
                    try:
                        if not expression.formula_expression.startswith('_report_handler_'):
                            formula = "result = {}".format(expression.formula_expression)
                            safe_eval(formula, variables, mode='exec', nocopy=True)
                            variables[expression.name] = variables.get('result', False)

                            expression_domain = report_group_domain
                            if expression.computation_engine == 'domain':
                                expression_domain = group.get('__domain', [])

                            expression_value = expression._parse_expression_value(variables, variables.get(expression.name), root_domain=expression_domain, report_group=report_group)

                            # If value is aggregate and passed from group allowing to use that value if expression not returning any result
                            if expression.allow_aggregate and not expression_value and group.get(expression.name):
                                expression_value = group.get(expression.name)

                            variables['sum'] = expression_value
                            variables[expression.name] = expression_value

                        try:
                            if expression.subformula_expression:
                                subformula = "result = {}".format(expression.subformula_expression)
                                safe_eval(subformula, variables, mode='exec', nocopy=True)
                                variables[expression.name] = variables.get('result')
                        except Exception:
                            _logger.warning('Subformula_expression failed {}'.format(traceback.format_exc()))

                        group_value[expression.name] = expression._parse_display_value(group, variables.get(expression.name), variables)
                        group_value['{}_original'.format(expression.name)] = variables.get(expression.name)
                        group_value['{}_is_zero'.format(expression.name)] = bool(variables.get(expression.name) in ['', 0, None])
                    except Exception as e:
                        traceback.print_exc()
                        _logger.warning("_get_grouping_data: {}".format(str(e)))
                        group_value[expression.name] = expression._parse_expression_value(variables, False)
                        group_value['{}_original'.format(expression.name)] = False

                    # Filter Domain
                    group_value.update({'_filter_domain': report_group_domain})

                # Updating report group values
                report_group_values.update({
                    report_group_key: group_value
                })

            id = None
            title = None
            if group_by == 'id':
                id, title = group.get('id'), group.get('display_name', group.get('name'))
            else:
                if group_by and group.get(group_by):
                    if isinstance(group.get(group_by), tuple):
                        id, title = group.get(group_by)
                    elif isinstance(group.get(group_by), int):
                        group_by_field = self.env[self.model_name]._fields[group_by]
                        if group_by_field.type == 'many2one':
                            rec = self.sudo().env[group_by_field.comodel_name].sudo().with_context(prefetch_fields=False).browse(group.get(group_by))
                            id, title = rec and (rec.id, rec.display_name) or (False, _('Unknown'))
                    else:
                        id, title = group.get('id'), group.get(group_by, _('Unknown'))

            action_value = self._get_action() if not bool(sub_group_by and sub_group_by.strip()) else False

            records.append({
                'id': id or '{}.{}'.format(group_by, self.id),
                'report_line_id': self.id,
                'title': kwargs.get('title', title or self.name) if sub_group_by and group_by != 'id' else title,
                'code': group_by,
                'level': self.hierarchy_level + kwargs.get('level', 1),
                'foldable': bool(sub_group_by and sub_group_by.strip()) if not kwargs.get('no_action') else False,
                'action': action_value if not kwargs.get('no_action') else False,
                'group_by': sub_group_by,
                'children': [],
                'line_id': self.id,
                '_filter_domain': group.get('__domain', []),
                'current_group_by': group_by,
                'values': report_group_values,
                'group_total': kwargs.get('group_total', False),
                'row_class': 'ics_group_total' if kwargs.get('group_total', False) else '',
                **extra_params
            })
        if options.get('orderby'):
            return sorted(records, key=lambda x: x['values']['main_group'][f"{options.get('orderby')}_original"], reverse=options.get('reverse'))
        return records

    def _get_grouping_data(self, group_by, sub_group_by, options, domain=[], **kwargs):
        self.ensure_one()
        records = []

        domain = domain + self.web_report_id._get_default_domain(options, ignore_date_domain=not self.strict_on_date_range, **kwargs)

        data_fields = self.expression_ids.filtered(lambda exp: exp.computation_engine == 'field').mapped('name')

        groups, sub_group_by = self._get_group_data(data_fields, domain, group_by, sub_group_by, options, **kwargs)

        report_groups = options.get('report_header_groups', {})

        report_handler = self.web_report_id._get_report_handler()

        for idx, group in enumerate(groups):
            report_group_values = {}
            for report_group_key, report_group in report_groups.items():
                # clubbing report group and data group domain
                report_group_domain = report_group.get('__domain', []) + group.get('__domain', [])

                # Getting report group based data
                sub_groups = self._get_group_data(data_fields, report_group_domain, group_by, sub_group_by, options, **kwargs)[0]
                variables = {field_name: sub_groups and sub_groups[0].get(field_name) or False for field_name in data_fields}

                group_value = {}

                if self.web_report_id.enable_report_handler_code:
                    handler_code_result = self.web_report_id._compute_handler_code(dict(
                        web_report=self.web_report_id,
                        web_report_line=self,
                        record=group,
                        record_domain=report_group_domain,
                        options=options,
                        group_by=group_by,
                        sub_group_by=sub_group_by,
                        **kwargs
                    )) or {}
                    variables.update(handler_code_result)

                for expression in self.expression_ids:
                    try:
                        if report_handler is not None and expression.formula_expression.startswith('_report_handler_'):
                            if hasattr(report_handler, expression.formula_expression):
                                variables.update(getattr(report_handler, expression.formula_expression)(
                                    self.web_report_id,
                                    self,
                                    group,
                                    report_group_domain,
                                    options,
                                    group_by=group_by,
                                    sub_group_by=sub_group_by,
                                    report_group=report_group,
                                    previous_record=records[idx-1] if idx > 0 else False,
                                    report_group_key=report_group_key,
                                    **kwargs
                                ) or {})
                        else:
                            formula = "result = {}".format(expression.formula_expression)
                            safe_eval(formula, variables, mode='exec', nocopy=True)
                            variables[expression.name] = variables.get('result', False)

                            # Here, by default report_group_domain is including group + report header group
                            # which may include date filters
                            # we are supporting date scope in case of expression is domain based
                            # Skipping for that expression date filter domain which can be
                            # handled at expression level by date scope selected
                            expression_domain = report_group_domain
                            if expression.computation_engine == 'domain':
                                expression_domain = group.get('__domain', [])

                            expression_value = expression._parse_expression_value(
                                variables,
                                variables.get(expression.name),
                                report_group=report_group,
                                root_domain=expression_domain
                            )

                            variables['sum'] = expression_value
                            variables[expression.name] = expression_value

                        try:
                            if expression.subformula_expression:
                                subformula = "result = {}".format(expression.subformula_expression)
                                safe_eval(subformula, variables, mode='exec', nocopy=True)
                                variables[expression.name] = variables.get('result')
                        except Exception:
                            _logger.warning('Subformula_expression failed {}'.format(traceback.format_exc()))

                        group_value[expression.name] = expression._parse_display_value(group, variables.get(expression.name), variables)
                        group_value['{}_original'.format(expression.name)] = variables.get(expression.name)
                        group_value['{}_is_zero'.format(expression.name)] = bool(variables.get(expression.name) in ['', 0, None])
                    except Exception as e:
                        traceback.print_exc()
                        _logger.warning("_get_grouping_data: {}".format(str(e)))
                        group_value[expression.name] = expression._parse_expression_value(variables, False)
                        group_value['{}_original'.format(expression.name)] = False

                    # Filter Domain
                    group_value.update({'_filter_domain': report_group_domain})

                # Updating report group values
                report_group_values.update({
                    report_group_key: group_value
                })

            if group_by == 'id':
                id, title = group.get('id'), group.get('display_name', group.get('name'))
            else:
                id, title = group.get(group_by) if group_by else (self.id, self.name)

            # Overriding dynamic title from expression
            if report_group_values.get('main_group', {}).get('title'):
                title = report_group_values.get('main_group', {}).get('title')

            redirect_action = self._get_action() if not bool(sub_group_by and sub_group_by.strip()) else False

            records.append({
                'id': id or '{}.{}'.format(group_by, self.id),
                'res_id': group.get('res_id', id),
                'report_line_id': self.id,
                'title': kwargs.get('title', title or self.name) if sub_group_by and group_by != 'id' else title,
                'code': group_by,
                'level': self.hierarchy_level + kwargs.get('level', 1),
                'foldable': bool(sub_group_by and sub_group_by.strip()),
                'action': redirect_action,
                'group_by': sub_group_by,
                'children': [],
                'line_id': self.id,
                '_filter_domain': group.get('__domain', []),
                'current_group_by': group_by,
                'values': report_group_values,
                'group_total': kwargs.get('group_total', False)
            })
        return records

    def _get_action(self):
        self.ensure_one()
        if self.action_id:
            record = self.env[self.action_id.type].sudo().browse(self.action_id.id)
            action = record.read()[0]
            return clean_action({
                field: value
                for field, value in action.items()
                if field in record._get_readable_fields()
            }, self.env)
        return False

    def _get_default_action_domain(self):
        self.ensure_one()
        return ast.literal_eval(self.default_action_domain or '[]')

    def action_redirect_to_action(self, record, report_options, kwargs):
        action = record.get('action', self._get_action())
        context = ast.literal_eval(action.get('context', '{}'))

        res_ids = []
        if self.action_field_id:
            field_name = self.action_field_id.name
            record_obj = self.env[self.model_name].browse(record.get('id'))
            res_ids = field_name in record_obj and record_obj[field_name].ids or []
            if res_ids and len(res_ids) <= 1:
                action['res_id'] = res_ids[0]
                action['view_id'] = False,
                action['views'] = [(False, 'form')]
            else:
                context.update({'domain': [('id', 'in', res_ids)]})
        else:
            context.update({'options': {
                key: values for key, values in report_options.items() if key in ['filter_date', 'filter_date_options', 'company_id', 'company_name']
            }})

        action['context'] = context
        return action
