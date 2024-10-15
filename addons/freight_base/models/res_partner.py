from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.phone_validation.tools import phone_validation
import re
from lxml import etree


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    # method is overridden because the city field is permanently made invisible
    @api.model
    def _fields_view_get_address(self, arch):
        if self.env.context.get('no_address_format'):  # remove super from above line
            return arch

        doc = etree.fromstring(arch)
        if doc.xpath("//field[@name='city_id']"):
            return arch

        # add invisible attribute in city field and remove invisible from attrs, and also remove invisible attrs from city_id, replace state_id field and add domain for city_id field
        replacement_xml = """
            <div>
                <field name="country_enforce_cities" invisible="1"/>
                <field name="type" invisible="1"/>
                <field name='city' placeholder="%(placeholder)s" class="o_address_city" invisible="1"
                    attrs="{
                        'readonly': [('type', '=', 'contact')%(parent_condition)s]
                    }"%(required)s
                />
                <field name='state_id' options="{'no_open': True, 'no_quick_create': True}" placeholder="State" string="State" class="o_address_state"
                    context="{'default_country_id': country_id}"
                    domain="[('country_id', '=', country_id)]"
                    attrs="{
                        'readonly': [('type', '=', 'contact'),('parent_id', '!=', False)]
                    }"
                />
                <field name='city_id' options="{'no_open': True}" placeholder="%(placeholder)s" string="%(placeholder)s" class="o_address_city"
                    context="{'default_country_id': country_id,
                              'default_name': city,
                              'default_zipcode': zip,
                              'default_state_id': state_id}"
                    domain="[('country_id', '=', country_id), ('state_id','=',state_id)]"
                    attrs="{
                        'readonly': [('type', '=', 'contact')%(parent_condition)s]
                    }"
                />
            </div>
        """

        replacement_data = {
            'placeholder': _('City'),
        }

        def _arch_location(node):
            in_subview = False
            view_type = False
            parent = node.getparent()
            while parent is not None and (not view_type or not in_subview):
                if parent.tag == 'field':
                    in_subview = True
                elif parent.tag in ['list', 'tree', 'kanban', 'form']:
                    view_type = parent.tag
                parent = parent.getparent()
            return {
                'view_type': view_type,
                'in_subview': in_subview,
            }

        for city_node in doc.xpath("//field[@name='city']"):
            location = _arch_location(city_node)
            replacement_data['parent_condition'] = ''
            replacement_data['required'] = ''
            if location['view_type'] == 'form' or not location['in_subview']:
                replacement_data['parent_condition'] = ", ('parent_id', '!=', False)"
            if 'required' in city_node.attrib:
                existing_value = city_node.attrib.get('required')
                replacement_data['required'] = f' required="{existing_value}"'

            replacement_formatted = replacement_xml % replacement_data
            for replace_node in etree.fromstring(replacement_formatted).getchildren():
                city_node.addprevious(replace_node)
            parent = city_node.getparent()
            parent.remove(city_node)

        arch = etree.tostring(doc, encoding='unicode')
        return arch

    @api.depends('name')
    def _compute_customer_code(self):
        for record in self:
            customer_code = ''
            customer_code_number = 0
            contact_name = record.name
            if contact_name:
                name_prefix = ''.join([x[0].upper() for x in contact_name.split(' ') if x])
                name_prefix = "{}-".format(name_prefix)
                contact_search_domain = []
                # as some times, record pass with NewID, so we need to check that if record is not newly created,
                # then only its Id checking should be append in domain
                if record._origin:
                    contact_search_domain.append(('id', '!=', record._origin.id))
                contact_search_domain.extend([('customer_code', 'ilike', name_prefix), '|', ('active', '=', True), ('active', '=', False)])

                existing_prefix_contacts = self.sudo().search(contact_search_domain, order="customer_code_number desc", limit=1)
                if not existing_prefix_contacts:
                    customer_code_number = 1
                else:
                    customer_code_number = existing_prefix_contacts[0].customer_code_number + 1

                customer_code = "{}{}".format(name_prefix, customer_code_number)
            record.customer_code = customer_code
            record.customer_code_number = customer_code_number

    @api.depends('child_ids')
    def _compute_mark_as_default(self):
        for partner in self:
            mark_as_default = False
            if not partner.parent_id and not partner.child_ids:
                mark_as_default = True
            partner.mark_as_default = mark_as_default

    def _inverse_mark_as_default(self):
        for partner in self:
            if partner.mark_as_default:
                if partner.parent_id:
                    partner_ids = partner.parent_id + partner.parent_id.child_ids - partner
                    partner_ids = partner_ids.filtered(lambda p: p.mark_as_default)
                    partner_ids.mark_as_default = False
                else:
                    partner_ids = partner.child_ids.filtered(lambda p: p.mark_as_default)
                    partner_ids.mark_as_default = False

    category_ids = fields.Many2many('res.partner.type', string="Party Types")
    freight_carrier_id = fields.Many2one('freight.carrier')
    fax = fields.Char(string="Fax")
    addr_type = fields.Selection(
        selection=[
            ('invoice', 'Invoice Address'),
            ('delivery', 'Delivery Address'),
            ('sales', 'Sales'),
            ('comex', 'Comex'),
            ('customer_service', 'Customer Service'),
            ('import', 'Import'),
            ('export', 'Export'),
        ],
        string='Address Type',
        default='invoice',
        help="Invoice & Delivery addresses are used in sales orders."
    )
    type = fields.Selection(
        selection=[
            ('contact', 'Address'),
            ('invoice', 'Invoice Address'),
            ('delivery', 'Delivery Address'),
            ('other', 'Other Address'),
            ('private', 'Private Address')
        ],
        string='Contact Address Type',
        compute='_compute_type',
        inverse='_inverse_type',
        store=True,
    )
    # I have redefined this field to change the string of Address form view to 'Create Contact' to 'Create Address'.
    child_ids = fields.One2many('res.partner', 'parent_id', string='Address', domain=[('active', '=', True)])  # force "active_test" domain to bypass _search() override
    mark_as_default = fields.Boolean(compute="_compute_mark_as_default", inverse="_inverse_mark_as_default", store=True, readonly=False)
    customer_code = fields.Char(compute="_compute_customer_code", store=True)
    customer_code_number = fields.Integer(compute="_compute_customer_code", store=True, string="Customer Code Number")
    contact_person = fields.Char(copy=False)
    internal_ref_no = fields.Char(string='Internal Reference No.', copy=False, tracking=True)

    @api.depends('addr_type')
    def _compute_type(self):
        for record in self:
            if not record.type == 'contact':
                record.type = record.addr_type if record.addr_type in ['invoice', 'delivery'] else 'other'

    def _inverse_type(self):
        for record in self:
            if record.type in ['invoice', 'delivery']:
                record.addr_type = record.type

    @api.constrains('phone')
    def _check_phone_no(self):
        for rec in self.filtered(lambda r: r.phone):
            try:
                phone_validation.phone_format(rec.phone, rec.country_id.code, rec.country_id.phone_code, force_format=False)
            except Exception:
                raise ValidationError(_('Please enter a valid phone number'))

    @api.constrains('mobile')
    def _check_mobile_no(self):
        for rec in self.filtered(lambda r: r.mobile):
            try:
                phone_validation.phone_format(rec.mobile, rec.country_id.code, rec.country_id.phone_code, force_format=False)
            except Exception:
                raise ValidationError(_('Please enter a valid Mobile number'))

    @api.constrains('fax')
    def _check_fax_no(self):
        for rec in self.filtered(lambda r: r.fax):
            try:
                phone_validation.phone_format(rec.fax, rec.country_id.code, rec.country_id.phone_code, force_format='INTERNATIONAL')
            except Exception:
                raise ValidationError(_('Please enter a valid FAX number'))

    @api.constrains('email')
    def validate_mail(self):
        if self.email:
            for email in self.email.split(','):
                match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,5})$', str(email).strip().lower())
                if not match:
                    raise ValidationError('Not a valid E-mail ID')

    @api.model
    def get_import_templates(self):
        return self.env['base']._get_import_templates(self)

    @api.onchange('country_id')
    def onchange_country_id(self):
        if self.country_id:
            self.phone = ''
            self.mobile = ''
            if self.country_id != self.state_id.country_id:
                self.state_id = False
            if self.country_id != self.city_id.country_id:
                self.city_id = False
            self.zip = self.city_id.zipcode if self.city_id else False

    @api.onchange('state_id')
    def onchange_state_id(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id.id
        if self.city_id and self.city_id.state_id != self.state_id:
            self.city_id = False
        self.zip = self.city_id.zipcode if self.city_id else False

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id.state_id:
            self.state_id = self.city_id.state_id.id
        if self.city_id.country_id:
            self.country_id = self.city_id.country_id.id
        self.zip = self.city_id.zipcode if self.city_id else False

    @api.model
    def default_get(self, default_fields):
        values = super().default_get(default_fields)
        if 'parent_id' in default_fields and values.get('parent_id'):
            parent = self.browse(values.get('parent_id'))
            values.update({
                'street': parent.street,
                'street2': parent.street2,
                'city_id': parent.city_id.id,
                'zip': parent.zip,
                'state_id': parent.state_id.id,
                'country_id': parent.country_id.id,
            })
        return values

    def get_default_addresses(self):
        self.ensure_one()
        all_address = self + self.child_ids
        return all_address.filtered(lambda a: a.mark_as_default and a.company_id.id in [self.company_id.id, False]) or self

    @api.model_create_single
    def create(self, values):
        # set company is default when partner not created from user.
        if 'customer_rank' and 'supplier_rank' not in values and not self.env.context.get('create_company'):
            values.update({'company_id': self.env.company.id})
        return super().create(values)

    def check_duplicate_domain(self, name, email):
        domain = [('name', '=ilike', name)]
        if email:
            domain.append(('email', '=ilike', email))
        return domain

    @api.model
    def check_duplicate(self, record_id, name, email):
        domain = self.check_duplicate_domain(name, email)
        if record_id:
            domain += [('id', '!=', record_id)]
        return bool(self.search(domain))

    def _get_name(self):
        name = super()._get_name()
        if self.env.company.show_contact_prefix:
            partner = self
            name = '%s: %s' % (partner.customer_code or partner.parent_id.customer_code, name)
        return name


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.onchange('email')
    def validate_mail(self):
        if self.email:
            match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,5})$', str(self.email).lower())
            if not match:
                raise ValidationError('Not a valid E-mail ID')
