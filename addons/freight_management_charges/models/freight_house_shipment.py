from odoo import models, fields, api, _
from odoo.tools import format_decimalized_amount
from odoo.exceptions import ValidationError


class FreightHouseShipmentCharges(models.Model):
    _name = 'freight.house.shipment'
    _inherit = ['freight.house.shipment', 'shipment.profitability.mixin']

    # Revenue
    revenue_charge_ids = fields.One2many('house.shipment.charge.revenue', 'house_shipment_id', string='Revenue Charges')
    revenue_charge_count = fields.Integer(compute='_compute_revenue_charge_count', store=True)
    revenue_charge_amount = fields.Monetary(compute='_compute_revenue_charge_amount', store=True)
    revenue_charge_state_info = fields.Char(compute='_compute_revenue_charge_state_info', store=True)

    # Cost
    cost_charge_ids = fields.One2many('house.shipment.charge.cost', 'house_shipment_id', string='Cost Charges')
    cost_charge_count = fields.Integer(compute='_compute_cost_charge_count', store=True)
    cost_charge_amount = fields.Monetary(compute='_compute_cost_charge_amount', store=True)
    cost_charge_state_info = fields.Char(compute='_compute_cost_charge_state_info', store=True)

    # Accounting
    move_line_ids = fields.One2many('account.move.line', 'house_shipment_id', string='Moves Lines')
    move_ids = fields.Many2many('account.move', compute='_compute_account_moves_count', store=True, string='Moves')
    invoice_count = fields.Integer(compute='_compute_account_moves_count', store=True)
    vendor_bill_count = fields.Integer(compute='_compute_account_moves_count', store=True)
    credit_note_count = fields.Integer(compute='_compute_account_moves_count', store=True)
    debit_note_count = fields.Integer(compute='_compute_account_moves_count', store=True)

    # Profitability
    # Estimated vs Received
    estimated_revenue = fields.Monetary(string='Estimated Revenue', compute='_compute_estimated_revenue', store=True)
    estimated_cost = fields.Monetary(string='Estimated Cost', compute='_compute_estimated_cost', store=True)
    received_revenue = fields.Monetary(string='Revenue Received', compute='_compute_received_revenue', store=True)
    paid_cost = fields.Monetary(string='Cost Paid', compute='_compute_paid_cost', store=True)

    @api.depends('move_line_ids', 'parent_id', 'parent_id.compute_move_ids')
    def _compute_account_moves_count(self):
        for rec in self:
            move_lines = rec.move_line_ids
            move_ids = move_lines.mapped('move_id')
            rec.move_ids = [(6, 0, move_ids.ids)]
            rec.invoice_count = len(rec.move_ids.filtered(lambda line: line.move_type == 'out_invoice'))
            rec.vendor_bill_count = len(rec.move_ids.filtered(lambda line: line.move_type == 'in_invoice'))
            rec.credit_note_count = len(rec.move_ids.filtered(lambda line: line.move_type == 'out_refund'))
            rec.debit_note_count = len(rec.move_ids.filtered(lambda line: line.move_type == 'in_refund'))

    @api.depends('revenue_charge_ids')
    def _compute_revenue_charge_count(self):
        for rec in self:
            rec.revenue_charge_count = len(rec.revenue_charge_ids)

    @api.onchange('client_id')
    def _onchange_client_id(self):
        for rec in self:
            if rec.invoice_count > 0:
                raise ValidationError("You cannot change the customer for House Shipments after an invoice has been created.")
        return super()._onchange_client_id()

    def write(self, vals):
        for rec in self:
            if vals.get('company_id') and rec.revenue_charge_ids and rec.revenue_charge_ids.filtered(lambda r: r.company_id.id != vals.get('company_id')):
                raise ValidationError(_('You can not change company once charges are added'))
            if vals.get('company_id') and rec.cost_charge_ids and rec.cost_charge_ids.filtered(lambda c: c.company_id.id != vals.get('company_id')):
                raise ValidationError(_('You can not change company once charges are added'))
        return super(FreightHouseShipmentCharges, self).write(vals)

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

    def action_open_moves(self):
        self.ensure_one()
        move_type = self.env.context.get('move_type')
        if not move_type or move_type == 'entry':
            return
        invoices = self.move_ids.filtered(lambda move: move.move_type == move_type)
        if not invoices:
            return
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_%s_type" % (move_type))
        action['context'] = {'default_house_shipment_id': self.id, 'default_move_type': move_type, 'create': 0}

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

    @api.depends('revenue_charge_ids', 'revenue_charge_ids.total_amount')
    def _compute_estimated_revenue(self):
        for shipment in self:
            shipment.estimated_revenue = sum(shipment.revenue_charge_ids.mapped('total_amount'))

    @api.depends('cost_charge_ids', 'cost_charge_ids.total_amount')
    def _compute_estimated_cost(self):
        for shipment in self:
            shipment.estimated_cost = sum(shipment.cost_charge_ids.mapped('total_amount'))

    @api.depends('revenue_charge_ids', 'revenue_charge_ids.total_amount', 'revenue_charge_ids.amount_currency_residual')
    def _compute_received_revenue(self):
        for shipment in self:
            total_amount = sum(shipment.revenue_charge_ids.mapped('total_amount'))
            due_amount = sum(shipment.revenue_charge_ids.mapped('total_residual_amount'))
            shipment.received_revenue = round(total_amount - due_amount, 3)

    @api.depends('cost_charge_ids', 'cost_charge_ids.total_amount', 'cost_charge_ids.amount_currency_residual')
    def _compute_paid_cost(self):
        for shipment in self:
            total_amount = sum(shipment.cost_charge_ids.mapped('total_amount'))
            due_amount = sum(shipment.cost_charge_ids.mapped('total_residual_amount'))
            shipment.paid_cost = round(total_amount - due_amount, 3)

    def action_detach_shipment_house(self):
        for house_shipment in self:

            # Raise validation when House charge created from Master with Generate Invoice from Master Enabled
            if house_shipment.parent_id.generate_invoice_from_master:
                house_charge_invoiced = house_shipment.revenue_charge_ids.filtered(
                    lambda charge: charge.status in charge._modification_line_restrict_states()
                )
                if house_charge_invoiced:
                    houses = house_shipment.mapped('name')
                    raise ValidationError(_('Unable to detach house shipment.\nCharges are already billed or partially invoiced from the master for the following house shipments:\n\n- {}'.format(
                        '\n- '.join(houses)
                    )))

            if house_shipment.parent_id.generate_invoice_from_master:
                house_charge_billed = house_shipment.cost_charge_ids.filtered(
                    lambda charge: charge.status in charge._modification_line_restrict_states()
                )
                if house_charge_billed:
                    houses = house_shipment.mapped('name')
                    raise ValidationError(_('Unable to detach house shipment.\nCharges are already billed or partially billed from the master for the following house shipments:\n\n- {}'.format(
                        '\n- '.join(houses)
                    )))

            # Removed Charges Adjusted from Master Shipment

            # Detaching and removing all adjusted Revenue from all houses
            # Note That, if single house is detach, all the adjusted lines to all houses need to remove
            # it also need to check, if any of the house's invoice generated user can not detach any house from
            # that master. User need to first remove that invoice and then user can detach house shipment
            master_revenue_charges = house_shipment.revenue_charge_ids.mapped('master_shipment_revenue_charge_id')
            house_charge_invoiced = master_revenue_charges.house_charge_revenue_ids.filtered(lambda charge: charge.status in charge._modification_line_restrict_states())
            if house_charge_invoiced:
                houses = house_charge_invoiced.mapped('house_shipment_id.name')
                raise ValidationError(_('Unable to detach house.\nMasters\'s Charges are already invoiced or partial invoiced in below houses.\n\n- {}'.format(
                    '\n- '.join(houses)
                )))
            else:
                # Also removing all adjusted charges as one of the house charge is remove other also need to remove
                master_revenue_charges.house_charge_revenue_ids.unlink()

            # Detaching and removing all adjusted Cost from all houses
            master_cost_charges = house_shipment.cost_charge_ids.mapped('master_shipment_cost_charge_id')
            house_charge_billed = master_cost_charges.house_charge_cost_ids.filtered(lambda charge: charge.status in charge._modification_line_restrict_states())
            if house_charge_billed:
                houses = house_charge_billed.mapped('house_shipment_id.name')
                raise ValidationError(_('Unable to detach house.\nMasters\'s Charges are already billed or partial billed in below houses.\n\n- {}'.format(
                    '\n- '.join(houses)
                )))
            else:
                # Also removing all adjusted charges as one of the house charge is remove other also need to remove
                master_cost_charges.house_charge_cost_ids.unlink()

        super().action_detach_shipment_house()

    def unlink(self):
        for shipment in self:
            billed_cost_charge_ids = shipment.cost_charge_ids\
                .filtered(lambda charge: charge.status in ['partial', 'fully_billed'])
            invoiced_revenue_charge_ids = shipment.revenue_charge_ids\
                .filtered(lambda charge: charge.status in ['partial', 'fully_invoiced'])
            if billed_cost_charge_ids or invoiced_revenue_charge_ids:
                raise ValidationError(_("You cannot do this modification on a shipment "
                                        "after charges are invoiced/billed."))
        return super().unlink()

    def action_view_house_shipment_revenue_charges(self):
        action = self.env.ref('freight_management_charges.freight_house_shipment_view_revenue_charges_action').sudo().read()[0]
        context = {}
        context.update({
            'default_house_shipment_id': self.id,
            'search_default_group_charge_type': True,
            'side_panel_view': 'freight_management.freight_house_shipment_info_view_form',
            'side_panel_res_id': self.id,
            'side_panel_model': 'freight.house.shipment',
            'create': self.state not in ['cancelled'] if not self.env.user.has_group('freight_management.group_super_admin') else True,
            'edit': self.state not in ['cancelled'] if not self.env.user.has_group('freight_management.group_super_admin') else True,
            'delete': self.state not in ['cancelled'] if not self.env.user.has_group('freight_management.group_super_admin') else True
        })
        action['context'] = context
        return action

    def action_view_house_shipment_cost_charges(self):
        action = self.env.ref('freight_management_charges.freight_house_shipment_view_cost_charges_action').sudo().read()[0]
        context = {}
        context.update({
            'default_house_shipment_id': self.id,
            'search_default_group_charge_type': True,
            'side_panel_view': 'freight_management.freight_house_shipment_info_view_form',
            'side_panel_res_id': self.id,
            'side_panel_model': 'freight.house.shipment',
            'create': self.state not in ['cancelled'] if not self.env.user.has_group('freight_management.group_super_admin') else True,
            'edit': self.state not in ['cancelled'] if not self.env.user.has_group('freight_management.group_super_admin') else True,
            'delete': self.state not in ['cancelled'] if not self.env.user.has_group('freight_management.group_super_admin') else True
        })
        action['context'] = context
        return action

    def copy_data(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if self.cargo_is_package_group:
            default['revenue_charge_ids'] = [(0, 0, revenue_charge.copy_data()[0]) for revenue_charge in self.revenue_charge_ids]
            default['cost_charge_ids'] = [(0, 0, cost_charge.copy_data()[0]) for cost_charge in self.cost_charge_ids]
        return super(FreightHouseShipmentCharges, self).copy_data(default)
