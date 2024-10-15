from odoo import models, fields, api, _
from odoo.tools import format_decimalized_amount
from odoo.exceptions import ValidationError


class FreightMasterShipmentCharges(models.Model):
    _name = 'freight.master.shipment'
    _inherit = ['freight.master.shipment', 'shipment.profitability.mixin']

    @api.depends('house_shipment_ids')
    def _compute_attached_house_shipment_ids(self):
        for master in self:
            master.attached_house_shipment_ids = master.house_shipment_ids

    # Revenue
    revenue_charge_ids = fields.One2many('master.shipment.charge.revenue', 'master_shipment_id', string='Revenue Charges')
    revenue_charge_count = fields.Integer(compute='_compute_revenue_charge_count', store=True)
    revenue_charge_amount = fields.Monetary(compute='_compute_revenue_charge_amount', store=True)
    revenue_charge_state_info = fields.Char(compute='_compute_revenue_charge_state_info', store=True)

    # Cost
    cost_charge_ids = fields.One2many('master.shipment.charge.cost', 'master_shipment_id', string='Cost Charges')
    cost_charge_count = fields.Integer(compute='_compute_cost_charge_count', store=True)
    cost_charge_amount = fields.Monetary(compute='_compute_cost_charge_amount', store=True)
    cost_charge_state_info = fields.Char(compute='_compute_cost_charge_state_info', store=True)

    # Profitability
    # Estimated vs Received
    estimated_revenue = fields.Monetary(string='Estimated Revenue', compute='_compute_estimated_revenue', store=True)
    estimated_cost = fields.Monetary(string='Estimated Cost', compute='_compute_estimated_cost', store=True)

    move_line_ids = fields.One2many('account.move.line', 'master_shipment_id', string='Moves Lines')
    compute_move_ids = fields.Many2many('account.move', compute='_compute_invoice_from_house_shipment', store=True)
    generate_invoice_from_master = fields.Boolean(string='Generate Invoice From Master', copy=False, readonly=True, states={'draft': [('readonly', False)]}, default=True)
    house_shipment_invoice_count = fields.Integer(compute='_compute_house_shipment_account_moves_count')
    house_shipment_vendor_bill_count = fields.Integer(compute='_compute_house_shipment_account_moves_count')
    house_shipment_credit_note_count = fields.Integer(compute='_compute_house_shipment_account_moves_count')
    house_shipment_debit_note_count = fields.Integer(compute='_compute_house_shipment_account_moves_count')
    house_shipment_revenue_charges_count = fields.Integer(compute='_compute_house_shipment_revenue_charges')
    house_shipment_cost_charges_count = fields.Integer(compute='_compute_house_shipment_cost_charges')
    house_shipment_revenue_charge_state_info = fields.Char(compute='_compute_house_shipment_revenue_charge_state_info')
    house_shipment_cost_charge_state_info = fields.Char(compute='_compute_house_shipment_cost_charge_state_info')
    attached_house_shipment_ids = fields.Many2many("freight.house.shipment", 'attached_house_master_rel',
                                                   string="Attached Houses",
                                                   compute="_compute_attached_house_shipment_ids",
                                                   store=True)

    @api.depends('generate_invoice_from_master', 'house_shipment_ids', 'house_shipment_ids.move_ids', 'move_line_ids')
    def _compute_invoice_from_house_shipment(self):
        for rec in self:
            compute_move_ids = self.env['account.move.line']

            if rec.house_shipment_ids:
                compute_move_ids = rec.house_shipment_ids.mapped('move_ids')

            if rec.move_line_ids:
                move_lines = rec.move_line_ids
                compute_move_ids |= move_lines.mapped('move_id')

            rec.compute_move_ids = [(6, 0, compute_move_ids.ids)]

    def write(self, vals):
        for rec in self:
            if vals.get('company_id') and rec.revenue_charge_ids and rec.revenue_charge_ids.filtered(lambda r: r.company_id.id != vals.get('company_id')):
                raise ValidationError(_('You can not change company once charges are added'))
            if vals.get('company_id') and rec.cost_charge_ids and rec.cost_charge_ids.filtered(lambda c: c.company_id.id != vals.get('company_id')):
                raise ValidationError(_('You can not change company once charges are added'))
        return super(FreightMasterShipmentCharges, self).write(vals)

    @api.depends('revenue_charge_ids')
    def _compute_revenue_charge_count(self):
        for rec in self:
            rec.revenue_charge_count = len(rec.revenue_charge_ids)

    @api.depends('revenue_charge_ids', 'revenue_charge_ids.total_amount')
    def _compute_revenue_charge_amount(self):
        for rec in self:
            rec.revenue_charge_amount = sum(rec.revenue_charge_ids.mapped('total_amount'))

    @api.depends('revenue_charge_amount', 'revenue_charge_count')
    def _compute_revenue_charge_state_info(self):
        for rec in self:
            amount_display = format_decimalized_amount(rec.revenue_charge_amount, rec.currency_id)
            rec.revenue_charge_state_info = "{} ({})".format(amount_display, rec.revenue_charge_count)

    @api.depends('cost_charge_ids')
    def _compute_cost_charge_count(self):
        for rec in self:
            rec.cost_charge_count = len(rec.cost_charge_ids)

    @api.depends('cost_charge_ids', 'cost_charge_ids.total_amount')
    def _compute_cost_charge_amount(self):
        for rec in self:
            rec.cost_charge_amount = sum(rec.cost_charge_ids.mapped('total_amount'))

    @api.depends('cost_charge_amount', 'cost_charge_count')
    def _compute_cost_charge_state_info(self):
        for rec in self:
            amount_display = format_decimalized_amount(rec.cost_charge_amount, rec.currency_id)
            rec.cost_charge_state_info = "{} ({})".format(amount_display, rec.cost_charge_count)

    @api.depends('revenue_charge_ids', 'revenue_charge_ids.total_amount')
    def _compute_estimated_revenue(self):
        for shipment in self:
            shipment.estimated_revenue = sum(shipment.revenue_charge_ids.mapped('total_amount'))

    @api.depends('cost_charge_ids', 'cost_charge_ids.total_amount')
    def _compute_estimated_cost(self):
        for shipment in self:
            shipment.estimated_cost = sum(shipment.cost_charge_ids.mapped('total_amount'))

    def action_view_profitability(self):
        self.ensure_one()
        return {
            'name': _('Profitability'),
            'type': 'ir.actions.act_window',
            'res_model': 'house.cost.revenue.report',
            'view_mode': 'tree,pivot',
            'views': [[False, 'list'], [False, 'pivot']],
            'domain': [('house_shipment_id', 'in', self.house_shipment_ids.ids)],
            'context': {
                'create': 0,
                'delete': 0,
                'group_by': ['house_shipment_id', 'product_id'],
            },
        }

    def unlink(self):
        for shipment in self:
            adjusted_revenue_charge_ids = shipment.revenue_charge_ids\
                .filtered(lambda charge: charge.status == "adjusted")
            adjusted_cost_charge_ids = shipment.cost_charge_ids.filtered(
                lambda charge: charge.status == "adjusted")
            if adjusted_revenue_charge_ids or adjusted_cost_charge_ids:
                raise ValidationError(_("You cannot do this modification on a master shipment "
                                        "after charges are adjusted to house shipments."))
        return super().unlink()

    @api.depends('compute_move_ids')
    def _compute_house_shipment_account_moves_count(self):
        for rec in self:
            rec.house_shipment_invoice_count = len(rec.mapped('compute_move_ids').filtered(lambda m: m.move_type == 'out_invoice'))
            rec.house_shipment_vendor_bill_count = len(rec.mapped('compute_move_ids').filtered(lambda m: m.move_type == 'in_invoice'))
            rec.house_shipment_credit_note_count = len(rec.mapped('compute_move_ids').filtered(lambda m: m.move_type == 'out_refund'))
            rec.house_shipment_debit_note_count = len(rec.mapped('compute_move_ids').filtered(lambda m: m.move_type == 'in_refund'))

    def action_open_moves(self):
        self.ensure_one()
        move_type = self.env.context.get('move_type')
        if not move_type or move_type == 'entry':
            return
        invoices = self.mapped('compute_move_ids')
        invoices = invoices.filtered(lambda move: move.move_type == move_type)
        if not invoices:
            return
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_%s_type" % (move_type))
        action['context'] = {'default_move_type': move_type, 'create': 0}

        if len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
        return action

    @api.depends('house_shipment_ids')
    def _compute_house_shipment_revenue_charges(self):
        for rec in self:
            rec.house_shipment_revenue_charges_count = sum(rec.house_shipment_ids.mapped('revenue_charge_count'))

    @api.depends('house_shipment_ids')
    def _compute_house_shipment_cost_charges(self):
        for rec in self:
            rec.house_shipment_cost_charges_count = sum(rec.house_shipment_ids.mapped('cost_charge_count'))

    @api.depends('house_shipment_revenue_charges_count')
    def _compute_house_shipment_revenue_charge_state_info(self):
        for rec in self:
            total_revenue_charge_amount = sum(rec.house_shipment_ids.mapped('revenue_charge_amount'))
            amount_display = format_decimalized_amount(total_revenue_charge_amount, rec.currency_id)
            rec.house_shipment_revenue_charge_state_info = "{} ({})".format(amount_display, rec.house_shipment_revenue_charges_count)

    @api.depends('house_shipment_cost_charges_count')
    def _compute_house_shipment_cost_charge_state_info(self):
        for rec in self:
            total_cost_charge_amount = sum(rec.house_shipment_ids.mapped('cost_charge_amount'))
            amount_display = format_decimalized_amount(total_cost_charge_amount, rec.currency_id)
            rec.house_shipment_cost_charge_state_info = "{} ({})".format(amount_display, rec.house_shipment_cost_charges_count)

    def action_open_freight_house_revenue(self):
        self.ensure_one()
        house_shipment_charges_revenue_ids = self.env['house.shipment.charge.revenue']
        for house_shipment in self.house_shipment_ids:
            house_shipment_charges_revenue_ids |= house_shipment.revenue_charge_ids

        tree_view_ref = self.env.ref('freight_management_charges.freight_house_charge_revenue_view_tree_inherit_direct_create')
        form_view_ref = self.env.ref('freight_management_charges.freight_house_charge_revenue_view_form_inherit_direct_create')
        return self.action_open_house_shipment_cost_revenue('Revenue Charges', tree_view_ref, form_view_ref, house_shipment_charges_revenue_ids)

    def action_open_freight_house_cost(self):
        self.ensure_one()
        house_shipment_charges_cost_ids = self.env['house.shipment.charge.cost']
        for house_shipment in self.house_shipment_ids:
            house_shipment_charges_cost_ids |= house_shipment.cost_charge_ids

        tree_view_ref = self.env.ref('freight_management_charges.freight_house_charge_cost_view_tree_inherit_direct_create')
        form_view_ref = self.env.ref('freight_management_charges.freight_house_charge_cost_view_form_inherit_direct_create')
        return self.action_open_house_shipment_cost_revenue('Cost Charges', tree_view_ref, form_view_ref, house_shipment_charges_cost_ids)

    def action_open_house_shipment_cost_revenue(self, name, tree_view_id, form_view_id, record_ids):
        self.ensure_one()
        return {
            'name': _(name),
            'type': 'ir.actions.act_window',
            'res_model': record_ids._name,
            'view_mode': 'tree,form',
            'views': [[tree_view_id.id, 'list'], [form_view_id.id, 'form']],
            'domain': [('parent_id', '=', self.id)],
            'context': {
                'default_parent_id': self.id,
                'search_default_group_by_house': True,
                'create': self.state not in ['cancelled'] if not self.env.user.has_group(
                    'freight_management.group_super_admin') else True,
                'edit': self.state not in ['cancelled'] if not self.env.user.has_group(
                    'freight_management.group_super_admin') else True,
                'delete': self.state not in ['cancelled'] if not self.env.user.has_group(
                    'freight_management.group_super_admin') else True
            },
        }

    @api.model
    def get_transporter_booking(self, domain=[], limit=10, offset=0, **kwargs):
        return []

    def action_open_freight_master_shipment_cost_charges(self):
        action = self.env.ref('freight_management_charges.freight_master_shipment_view_cost_charges_action').sudo().read()[0]
        context = {}
        context.update({
            'default_master_shipment_id': self.id,
            'search_default_group_charge_type': True,
            'side_panel_view': 'freight_management.freight_master_shipment_info_view_form',
            'side_panel_res_id': self.id,
            'side_panel_model': 'freight.master.shipment',
            'create': self.state not in ['cancelled'] if not self.env.user.has_group(
                'freight_management.group_super_admin') else True,
            'edit': self.state not in ['cancelled'] if not self.env.user.has_group(
                'freight_management.group_super_admin') else True,
            'delete': self.state not in ['cancelled'] if not self.env.user.has_group(
                'freight_management.group_super_admin') else True
        })
        action['context'] = context
        return action

    def action_open_freight_master_shipment_revenue_charges(self):
        action = self.env.ref('freight_management_charges.freight_master_shipment_view_revenue_charges_action').sudo().read()[0]
        context = {}
        context.update({
            'default_master_shipment_id': self.id,
            'search_default_group_charge_type': True,
            'side_panel_view': 'freight_management.freight_master_shipment_info_view_form',
            'side_panel_res_id': self.id,
            'side_panel_model': 'freight.master.shipment',
            'create': self.state not in ['cancelled'] if not self.env.user.has_group(
                'freight_management.group_super_admin') else True,
            'edit': self.state not in ['cancelled'] if not self.env.user.has_group(
                'freight_management.group_super_admin') else True,
            'delete': self.state not in ['cancelled'] if not self.env.user.has_group(
                'freight_management.group_super_admin') else True
        })
        action['context'] = context
        return action
