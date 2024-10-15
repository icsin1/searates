# -*- coding: utf-8 -*-

import itertools
from itertools import repeat
from odoo import models, fields, api, _
from odoo.tools import partition
from odoo.addons.base.models.res_users import parse_m2m, is_boolean_group, is_selection_groups, get_selection_groups, get_boolean_group, is_reified_group, name_boolean_group, name_selection_groups


class ResUserRole(models.Model):
    _name = "res.user.role"
    _description = 'Department'

    name = fields.Char(required=True)
    groups_id = fields.Many2many('res.groups', 'role_res_groups_users_rel', 'uid', 'gid', string='Groups', required=True)
    user_ids = fields.One2many('res.users', 'user_role_id', string='Allowed Users')
    user_count = fields.Integer(compute='_compute_user_count')
    active = fields.Boolean(default=True)

    @api.model
    def default_get(self, fields):
        group_fields, fields = partition(is_reified_group, fields)
        fields1 = (fields + ['groups_id']) if group_fields else fields
        values = super(ResUserRole, self).default_get(fields1)
        self._add_reified_groups(group_fields, values)
        return values

    def onchange(self, values, field_name, field_onchange):
        field_onchange['groups_id'] = ''
        result = super().onchange(values, field_name, field_onchange)
        if not field_name:  # merged default_get
            self._add_reified_groups(
                filter(is_reified_group, field_onchange),
                result.setdefault('value', {})
            )
        return result

    def read(self, fields=None, load='_classic_read'):
        # determine whether reified groups fields are required, and which ones
        fields1 = fields or list(self.fields_get())
        group_fields, other_fields = partition(is_reified_group, fields1)

        # read regular fields (other_fields); add 'groups_id' if necessary
        drop_groups_id = False
        if group_fields and fields:
            if 'groups_id' not in other_fields:
                other_fields.append('groups_id')
                drop_groups_id = True
        else:
            other_fields = fields

        res = super(ResUserRole, self).read(other_fields, load=load)

        # post-process result to add reified group fields
        if group_fields:
            for values in res:
                self._add_reified_groups(group_fields, values)
                if drop_groups_id:
                    values.pop('groups_id', None)
        return res

    def _remove_reified_groups(self, values):
        """ return `values` without reified group fields """
        add, rem = [], []
        values1 = {}

        for key, val in values.items():
            if is_boolean_group(key):
                (add if val else rem).append(get_boolean_group(key))
            elif is_selection_groups(key):
                rem += get_selection_groups(key)
                if val:
                    add.append(val)
            else:
                values1[key] = val

        if 'groups_id' not in values and (add or rem):
            # remove group ids in `rem` and add group ids in `add`
            values1['groups_id'] = list(itertools.chain(
                zip(repeat(3), rem),
                zip(repeat(4), add)
            ))

        return values1

    @api.model_create_single
    def create(self, values):
        record = super().create(self._remove_reified_groups(values))
        record.with_context(internal_user=True).write({'groups_id': [(4, self.env.ref('base.group_user').id)]})
        return record

    def write(self, vals):
        vals = self._remove_reified_groups(vals)
        if not self.env.context.get('internal_user'):
            groups = vals.get('groups_id', [])
            groups += [(4, self.env.ref('base.group_user').id)]
            vals['groups_id'] = groups
        return super().write(vals)

    @api.model
    def new(self, values={}, origin=None, ref=None):
        values = self._remove_reified_groups(values)
        return super().new(values=values, origin=origin, ref=ref)

    @api.depends('user_ids')
    def _compute_user_count(self):
        for rec in self:
            rec.user_count = len(rec.user_ids)

    def _add_reified_groups(self, fields, values):
        """ add the given reified group fields into `values` """
        gids = set(parse_m2m(values.get('groups_id') or []))
        for f in fields:
            if is_boolean_group(f):
                values[f] = get_boolean_group(f) in gids
            elif is_selection_groups(f):
                # determine selection groups, in order
                sel_groups = self.env['res.groups'].sudo().browse(get_selection_groups(f))
                sel_order = {g: len(g.trans_implied_ids & sel_groups) for g in sel_groups}
                sel_groups = sel_groups.sorted(key=sel_order.get)
                # determine which ones are in gids
                selected = [gid for gid in sel_groups.ids if gid in gids]
                # if 'Internal User' is in the group, this is the "User Type" group
                # and we need to show 'Internal User' selected, not Public/Portal.
                if self.env.ref('base.group_user').id in selected:
                    values[f] = self.env.ref('base.group_user').id
                else:
                    values[f] = selected and selected[-1] or False

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if fields:
            # ignore reified fields
            fields = [fname for fname in fields if not is_reified_group(fname)]
        return super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(ResUserRole, self).fields_get(allfields, attributes=attributes)
        # add reified groups fields
        for app, kind, gs, category_name in self.env['res.groups'].sudo().get_groups_by_application():
            if kind == 'selection':
                # 'User Type' should not be 'False'. A user is either 'employee', 'portal' or 'public' (required).
                selection_vals = [(False, '')]
                if app.xml_id == 'base.module_category_user_type':
                    selection_vals = []
                field_name = name_selection_groups(gs.ids)
                if allfields and field_name not in allfields:
                    continue
                # selection group field
                tips = ['%s: %s' % (g.name, g.comment) for g in gs if g.comment]
                res[field_name] = {
                    'type': 'selection',
                    'string': app.name or _('Other'),
                    'selection': selection_vals + [(g.id, g.name) for g in gs],
                    'help': '\n'.join(tips),
                    'exportable': False,
                    'selectable': False,
                }
            else:
                # boolean group fields
                for g in gs:
                    field_name = name_boolean_group(g.id)
                    if allfields and field_name not in allfields:
                        continue
                    res[field_name] = {
                        'type': 'boolean',
                        'string': g.name,
                        'help': g.comment,
                        'exportable': False,
                        'selectable': False,
                    }
        return res


class UserAccess(models.TransientModel):
    _name = "user.access.wizard"
    _description = 'User Access Wizard'

    def _get_user_ids(self):
        if self._context.get('active_ids'):
            return self.env['res.users'].browse(self._context.get('active_ids'))
        return False

    user_ids = fields.Many2many('res.users', string='Users', default=_get_user_ids)
    user_role_id = fields.Many2one('res.user.role', string='User Role')

    def action_grant_access(self):
        return self.user_ids.write({'user_role_id': self.user_role_id.id})
