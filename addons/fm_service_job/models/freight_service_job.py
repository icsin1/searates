import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from lxml import etree
import json

_logger = logging.getLogger(__name__)


SERVICE_JOB_STATE = [
    ('created', 'Created'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
]
WEIGHT_VOLUME_TRACK_FIELDS = [
    'pack_unit',
    'pack_unit_uom_id',
    'gross_weight_unit',
    'gross_weight_unit_uom_id',
    'weight_volume_unit',
    'weight_volume_unit_uom_id',
    'net_weight_unit',
    'net_weight_unit_uom_id',
    'volume_unit',
    'volume_unit_uom_id',
    'chargeable_kg',
]

READONLY_STAGE = {'created': [('readonly', False)]}


class FreightServiceJob(models.Model):
    _name = 'freight.service.job'
    _description = 'Freight Service Job'
    _inherit = ['freight.service.job.mixin', 'freight.customer.mixin', 'freight.shipper.mixin', 'freight.consignee.mixin']
    _rec_name = 'display_name'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):

        res = super(FreightServiceJob, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form' and not self.env.user.has_group('fm_service_job.group_super_admin'):
            for node in doc.xpath("//field"):
                modifiers = json.loads(node.get("modifiers"))
                if 'readonly' not in modifiers:
                    modifiers['readonly'] = [['state', 'in', ['cancelled', 'completed']]]
                else:
                    if type(modifiers['readonly']) != bool:
                        modifiers['readonly'].insert(-1, '|')
                        modifiers['readonly'] += [['state', 'in', ['cancelled', 'completed']]]
                node.set('modifiers', json.dumps(modifiers))
                res['arch'] = etree.tostring(doc)
        return res

    display_name = fields.Char(compute='_compute_display_name', store=True)
    name = fields.Char(related='booking_nomination_no', store=True, string='Booking Ref')
    booking_nomination_no = fields.Char(string='Booking Ref.', store=True, copy=False, default='New', readonly=True)
    service_job_number = fields.Char('Service Job No', copy=False, states=READONLY_STAGE, readonly=True)
    service_job_type_id = fields.Many2one('freight.job.type', states=READONLY_STAGE, readonly=True, ondelete='restrict')

    # Customer
    client_id = fields.Many2one('res.partner', states=READONLY_STAGE)
    client_address_id = fields.Many2one('res.partner', states=READONLY_STAGE)

    # Shipper and Consignee
    shipper_id = fields.Many2one('res.partner', states=READONLY_STAGE)
    shipper_address_id = fields.Many2one('res.partner', states=READONLY_STAGE)
    consignee_id = fields.Many2one('res.partner', states=READONLY_STAGE)
    consignee_address_id = fields.Many2one('res.partner', states=READONLY_STAGE)

    # Additional
    # HAZ Details
    is_hazardous = fields.Boolean(string='Is HAZ')
    haz_class_id = fields.Many2one('haz.sub.class.code', string='HAZ Class')
    haz_un_number = fields.Char(string='UN #')
    haz_remark = fields.Text('HAZ Remark')

    # Customs
    has_customs = fields.Boolean(default=False, string="Is Custom Required?")
    customs_ad_code = fields.Char(string='AD Code')
    customs_location_id = fields.Many2one('freight.custom.location', string='Custom Location')
    customs_declaration_number = fields.Char(string='Declaration Number')
    customs_declaration_date = fields.Date('Declaration Date')
    customs_clearance_datetime = fields.Datetime('Custom Clearance Date & Time')
    tariff_determination_number = fields.Char('Tariff Determination Number(TDN)')
    value_determination_number = fields.Char('Value Determination Number(VDN)')
    customs_procedure_code = fields.Char('Customs Procedure Code')
    # BOE Details
    boe_number = fields.Char(string='BOE Number', help="Bill of Entry Number", states=READONLY_STAGE)
    boe_date = fields.Date(string='BOE Date', help="Bill of Entry Date", states=READONLY_STAGE)
    ownership = fields.Selection(selection=[('self', 'Self'), ('third_party', 'Third Party')], default='self', states=READONLY_STAGE)
    ownership_id = fields.Many2one('res.partner', string='Ownership Name', domain=[('parent_id', '=', False)], states=READONLY_STAGE)
    # Documents
    customs_document_ids = fields.One2many('freight.service.job.customs.document', 'service_job_id', string='Custom Documents')

    # Partners/Parties
    service_job_partner_ids = fields.One2many(
        'freight.service.job.partner', 'service_job_id', string='Parties', states=READONLY_STAGE)

    # Events
    event_ids = fields.One2many('freight.service.job.event', 'service_job_id', string='Milestones Tracking')

    # Terms and Conditions
    terms_ids = fields.One2many('freight.service.job.terms', 'service_job_id', string='Terms & Conditions')

    # Documents
    document_ids = fields.One2many('freight.service.job.document', 'service_job_id', string='Documents')
    document_count = fields.Integer(compute='_compute_document_count')

    # Service Job State
    state = fields.Selection(SERVICE_JOB_STATE, default='created', tracking=True, group_expand='_expand_states')
    tag_ids = fields.Many2many('freight.shipment.tag', 'freight_service_job_tag_rel', 'service_job_id', 'tag_id', copy=False, string='Tags', states=READONLY_STAGE)

    # Readonly Abstract model column for Service Job
    company_id = fields.Many2one(states=READONLY_STAGE)
    date = fields.Date(states=READONLY_STAGE, default=lambda self: fields.Date.today())
    origin_un_location_id = fields.Many2one(states=READONLY_STAGE)
    destination_un_location_id = fields.Many2one(states=READONLY_STAGE)
    origin_port_un_location_id = fields.Many2one(states=READONLY_STAGE)
    destination_port_un_location_id = fields.Many2one(states=READONLY_STAGE)
    remarks = fields.Text("Remarks")
    customs_be_type_id = fields.Many2one('custom.master.be.type', string='BE Type')
    pickup_address = fields.Text('Pickup Address')
    delivery_address = fields.Text('Delivery Address')

    _sql_constraints = [
        ('name_unique', 'unique(booking_nomination_no,company_id)', 'The Booking Ref must be unique per Service-Job!'),
    ]

    @api.depends('service_job_number', 'booking_nomination_no')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.service_job_number or rec.booking_nomination_no

    @api.constrains('service_job_partner_ids')
    def _check_service_job_partner_ids(self):
        for service_job in self:
            existing_vendor_parties = []
            for party in service_job.service_job_partner_ids.filtered(lambda p: p.partner_type_id.is_vendor):
                if (party.partner_type_id.id, party.partner_id.id,) in existing_vendor_parties:
                    raise UserError(_('Vendor partner type with the same partner cannot be duplicated.'))
                existing_vendor_parties.append((party.partner_type_id.id, party.partner_id.id,))
            existing_other_parties = []
            for party in service_job.service_job_partner_ids.filtered(lambda p: not p.partner_type_id.is_vendor):
                if party.partner_type_id.id in existing_other_parties:
                    raise UserError(_('Only Single Non Vendor Partner Type Line Allowed.'))
                existing_other_parties.append(party.partner_type_id.id)

    def _expand_states(self, states, domain, order):
        return [key for key, dummy in type(self).state.selection]

    @api.constrains('service_job_number', 'state')
    def _check_unique_service_job_number(self):
        for service_job in self:
            if service_job.service_job_number:
                domain = [('service_job_number', '=ilike', service_job.service_job_number), ('id', '!=', service_job.id), ('company_id', '=', service_job.company_id.id)]
                if self.search_count(domain):
                    raise ValidationError(_('Service Job Number must be unique!'))
            else:
                if service_job.state != 'created':
                    raise ValidationError(_('Service Job Number is required.'))

    @api.onchange('client_id')
    def _onchange_client_id(self):
        super()._onchange_client_id()
        for rec in self:
            if rec.client_id and rec._context.get('force_change'):
                rec.ownership_id = rec.client_id.id
            rec.sales_agent_id = rec.client_id.user_id.id or self.env.user.id

    def _get_partner_field_list(self, values):
        self.ensure_one()
        return list(filter(
            lambda field: field in values and self._fields[field].comodel_name == 'res.partner', self._fields.keys()
        ))

    def _update_parties(self, vals):
        self.ensure_one()
        # Required sudo() as field level access is not granted to all users
        self = self.sudo()
        service_job_partners = []
        for partner_field in self._get_partner_field_list(vals):
            partner_id = self[partner_field]
            partner_type_field = self.env['res.partner.type.field'].sudo().search([('model_id.model', '=', self._name), ('field_id.name', '=', partner_field)], order="id desc", limit=1)
            if partner_field == 'client_id':
                address_id = self.client_address_id
            elif partner_field == 'shipper_id':
                address_id = self.shipper_address_id
            elif partner_field == 'consignee_id':
                address_id = self.consignee_address_id
            elif partner_field == 'client_address_id':
                address_id = self.client_address_id
                partner_id = self.client_id
            elif partner_field == 'shipper_address_id':
                address_id = self.shipper_address_id
                partner_id = self.shipper_id
            elif partner_field == 'consignee_address_id':
                address_id = self.consignee_address_id
                partner_id = self.consignee_id
            if partner_type_field:
                service_job_partner_exist = self.service_job_partner_ids.filtered(lambda party: party.partner_type_id.id == partner_type_field.type_id.id)
                if service_job_partner_exist:
                    service_job_partners.append((3, service_job_partner_exist.id) if not partner_id else (1, service_job_partner_exist.id, {
                        'partner_id': partner_id.id,
                        'party_address_id': address_id.id,
                    }))
                elif partner_id:
                    service_job_partners.append((0, 0, {
                        'partner_id': partner_id.id,
                        'partner_type_id': partner_type_field.type_id.id,
                        'party_address_id': address_id.id,
                    }))

        if service_job_partners:
            self.write({'service_job_partner_ids': service_job_partners})
        self.sync_party_address()

    def sync_party_address(self):
        for line in self.service_job_partner_ids:
            if line.partner_type_id == self.env.ref('freight_base.org_type_customer'):
                line.party_address_id = self.client_address_id.id
            if line.partner_type_id == self.env.ref('freight_base.org_type_shipper'):
                line.party_address_id = self.shipper_address_id.id
            if line.partner_type_id == self.env.ref('freight_base.org_type_consignee'):
                line.party_address_id = self.consignee_address_id.id

    @api.model_create_single
    def create(self, values):
        rec = super().create(values)
        rec._update_parties(values)
        rec._update_documents_list()
        return rec

    def _prepare_weight_volume_tracking_msg(self, tracking_fields):
        self.ensure_one()
        track_fields = tracking_fields[self.id]
        msg = "<p>Declared Weight & Volume</p>"
        msg += "<ul>"
        for field_name, value in track_fields.items():
            field_info = self.fields_get([field_name])[field_name]
            old_value = value
            new_value = self[field_name]
            if field_info.get('type') == "many2one":
                old_value = old_value.display_name
                new_value = new_value.display_name
            msg += """
                <li>
                    {}: {}
                    <span class="fa fa-long-arrow-right" style='vertical-align: middle;'/>
                    {}
                </li>""".format(field_info.get('string'), old_value, new_value)
        msg += "</ul>"
        return msg

    def _get_weight_volume_tracking(self, vals={}):
        self.ensure_one()
        tracking_fields_values = {}
        # if any of the vals keys is in tracking fields list
        updated_fields = set(vals.keys()).intersection(set(WEIGHT_VOLUME_TRACK_FIELDS))
        value_changed = False
        for updated_field in updated_fields:
            field_info = self.fields_get([updated_field])[updated_field]
            if field_info.get('type') == "many2one" and vals.get(updated_field) != self[updated_field].id:
                value_changed = True
            elif field_info.get('type') != "many2one" and vals.get(updated_field) != self[updated_field]:
                value_changed = True
        if updated_fields and value_changed:
            for key in WEIGHT_VOLUME_TRACK_FIELDS:
                tracking_fields_values.update({
                    key: self[key]
                })
        return tracking_fields_values

    def write(self, vals):
        tracking_fields = {}
        res = super().write(vals)
        for service_job in self:
            if not self._context.get('updated_from_line'):
                service_job._update_parties(vals)

            # Logging declared weight volume fields change log
            if tracking_fields.get(service_job.id):
                msg = service_job._prepare_weight_volume_tracking_msg(tracking_fields)
                service_job._message_log(body=msg,)
        return res

    def _update_documents_list(self):
        self.ensure_one()
        document_types = self.env['freight.document.type'].sudo().search([('model_id.model', '=', self._name)])
        documents = [(0, 0, {
            'name': doc_type.name,
            'document_type_id': doc_type.id,
            'datetime': self.create_date
        }) for doc_type in document_types]
        self.write({'document_ids': documents})

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    def action_service_job_documents(self):
        self.ensure_one()
        return {
            'name': _('Service Job Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.service.job.document',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('service_job_id', 'in', self.ids)],
            'context': {'default_service_job_id': self.id, 'search_default_group_by_mode': 1},
            'target': 'current',
        }

    def action_change_status(self):
        self.ensure_one()
        default_context = {
            'default_service_job_id': self.id, 'default_state': self.state
        }
        return {
            'name': 'Change Status',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.service.job.status',
            'context': default_context
        }
