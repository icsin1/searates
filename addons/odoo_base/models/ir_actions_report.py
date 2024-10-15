# -*- coding: utf-8 -*-
from odoo import models, fields


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    visibility = fields.Char(string='Main Visibility', copy=False, help="Initial Technical condition to define Report Visibility")
    report_label_ids = fields.One2many('report.visible.title', 'report_action_id', string='Report Visibility')


class ReportVisibleTitle(models.Model):
    _name = 'report.visible.title'
    _description = 'Report Title visibility'
    _order = 'sequence'

    sequence = fields.Integer(default=99)
    name = fields.Char(string='Label', copy=False, help="Report Label: Keep blank to Hide Report with Visibility Condition")
    visibility = fields.Char(string='Visibility', copy=False, help="Technical condition to define for the report Label based on action-context value")
    report_action_id = fields.Many2one('ir.actions.report')
