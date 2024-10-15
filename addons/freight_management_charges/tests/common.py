# -*- coding: utf-8 -*-
import logging
from odoo.tests.common import TransactionCase, tagged, Form

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class FreightShipmentCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Setup all shipment type data
        cls.setup_shipment_type_data()

        # Setup all freight transport data
        cls.setup_transport_mode_data()

        # Setup all cargo type data
        cls.setup_cargo_type_data()

        # Setup all Product data
        cls.setup_products()

        # Setup all Product data
        cls.setup_incoterms_data()

        # Create 'Customer' party type
        cls.customer_party_type = cls.setup_party_type_data('Customer',
                                                            model_name='freight.house.shipment',
                                                            field_name='client_id')

        # Create 'Shipper' party type
        cls.shipper_party_type = cls.setup_party_type_data('Shipper',
                                                           model_name='freight.house.shipment',
                                                           field_name='shipper_id')

        # Create 'Consignee' party type
        cls.consignee_party_type = cls.setup_party_type_data('Consignee',
                                                             model_name='freight.house.shipment',
                                                             field_name='consignee_id')

        # Create 'Vendor' party type
        cls.vendor_party_type = cls.setup_party_type_data('Vendor', vendor=True)

        # Create Partner data
        cls.partner_shipper_id = cls.setup_partner_data('Marc Demo')
        cls.partner_consignee_id = cls.setup_partner_data('George')
        cls.partner_client_id = cls.setup_partner_data('David')

        # Create Company
        cls.company = cls.setup_company_data('Marry Company',
                                             'MRYCO',
                                             'Asia/Kolkata',
                                             'base.INR')

        # Create record of fright.un.location for mundra, india.
        cls.inmun_port_location = cls.setup_freight_un_location_data('Mundra', 'INMUN', 'base.in')

        # Create record of fright.un.location for jebel ali, dubai.
        cls.aejea_port_location = cls.setup_freight_un_location_data('Jebel Ali', 'AEJEA', 'base.ae')

        # Create Freight Port
        cls.inmun_origin_port = cls.setup_freight_port_data('Mundra', 'Inmun', 'base.in', cls.sea_freight_mode)
        cls.aejea_destination_port = cls.setup_freight_port_data('AEJEA', 'AEJEA', 'base.ae', cls.sea_freight_mode)

        # Create Export Type House Shipment
        cls.export_house_shipment = cls.setup_house_shipment_data(cls.export_shipment_type,
                                                                  cls.fcl_sea_cargo_type,
                                                                  cls.sea_freight_mode,
                                                                  '2023-08-30', cls.incoterm_EXW,
                                                                  origin_port=cls.inmun_origin_port,
                                                                  destination_port=cls.aejea_destination_port)

        # Create Import Type House Shipment
        cls.import_house_shipment = cls.setup_house_shipment_data(cls.import_shipment_type,
                                                                  cls.lcl_sea_cargo_type,
                                                                  cls.sea_freight_mode,
                                                                  '2023-08-30', cls.incoterm_CFR,
                                                                  origin_port=cls.inmun_origin_port,
                                                                  destination_port=cls.aejea_destination_port)

        # Create Export FCL Type Master Shipment
        cls.export_fcl_master_shipment = cls.setup_master_shipment_data(cls.export_shipment_type,
                                                                        cls.fcl_sea_cargo_type,
                                                                        cls.sea_freight_mode,
                                                                        '2023-08-30',
                                                                        mbl_number='MBL-FCL-001')

        # Create Export LCL Type Master Shipment
        cls.export_lcl_master_shipment = cls.setup_master_shipment_data(cls.export_shipment_type,
                                                                        cls.lcl_sea_cargo_type,
                                                                        cls.sea_freight_mode,
                                                                        '2023-08-30',
                                                                        mbl_number='MBL-LCL-001')

    @classmethod
    def setup_currency_data(cls, currency_id_ref):
        """
        Get recordset of Currency from the data file for res.currency
        @param {string} currency_id_ref
        """
        return cls.env.ref(currency_id_ref)

    @classmethod
    def setup_country_data(cls, country_id_ref):
        """
        Get recordset of Country from the data file for res.country
        @param {string} country_id_ref
        """
        return cls.env.ref(country_id_ref)

    @classmethod
    def setup_company_data(cls, name, code, tz, currency_ref, **kwargs):
        """
        Create record of res.company

        @param {string} name
        @param {string} code
        @param {string} tz
        @param {string} currency_ref
        @returns {recordset}: record of 'res.partner.type'
        """
        # Get country id
        currency = cls.setup_currency_data(currency_ref)

        company_form = Form(cls.env["res.company"])
        company_form.name = name
        company_form.code = code
        company_form.tz = tz
        company_form.currency_id = currency

        return company_form.save()

    @classmethod
    def setup_shipment_type_data(cls):
        """
        Get recordset of Shipment Type from the data file for shipment.type
        """
        cls.export_shipment_type = cls.env.ref('freight_base.shipment_type_export')
        cls.import_shipment_type = cls.env.ref('freight_base.shipment_type_import')
        cls.cross_trade_shipment_type = cls.env.ref('freight_base.shipment_type_cross_trade')
        cls.domestic_shipment_type = cls.env.ref('freight_base.shipment_type_domestic')

    @classmethod
    def setup_transport_mode_data(cls):
        """
        Get recordset of transport mode from the data file for transport.mode
        """
        cls.sea_freight_mode = cls.env.ref('freight_base.transport_mode_sea')
        cls.air_freight_mode = cls.env.ref('freight_base.transport_mode_air')
        cls.land_freight_mode = cls.env.ref('freight_base.transport_mode_land')

    @classmethod
    def setup_party_type_data(cls, party_type, **kwargs):
        """
        Create record of res.partner.type

        @param {string} party_type
        @returns {recordset}: record of 'res.partner.type'
        """
        party_type_form = Form(cls.env["res.partner.type"])
        party_type_form.name = party_type

        # If party type is Vendor
        if kwargs.get('vendor'):
            party_type_form.is_vendor = kwargs.get('vendor')

        party_type = party_type_form.save()
        if kwargs.get('model_name') and kwargs.get('field_name'):
            with Form(party_type) as party_type_form:
                with party_type_form.field_mapping_ids.new() as field_mapped_line:
                    field_mapped_line.model_id = cls.env['ir.model']._get(kwargs.get('model_name'))
                    field_mapped_line.field_id = cls.env['ir.model.fields']._get(kwargs.get('model_name'),
                                                                                 kwargs.get('field_name'))
        return party_type

    @classmethod
    def setup_service_mode_data(cls, name, code, **kwargs):
        """
        Create record of freight.service.mode

        @param {string} name
        @param {string} code
        @returns {recordset}: record of 'freight.service.mode'
        """
        service_mode_form = Form(cls.env["freight.service.mode"])
        service_mode_form.name = name
        service_mode_form.code = code
        return service_mode_form.save()

    @classmethod
    def setup_freight_un_location_data(cls, name, code, country_ref, **kwargs):
        """
        Create record of freight.un.location (Origin and Destination place)

        @param {string} name
        @param {string} code
        @param {string} country_ref
        @returns {recordset}: record of 'freight.un.location'
        """
        un_location_obj = cls.env["freight.un.location"]
        un_location_id = un_location_obj.search([('loc_code', '=', code)])
        if un_location_id:
            return un_location_id

        # Get country id
        country_id = cls.setup_country_data(country_ref)
        un_location_form = Form(un_location_obj)
        un_location_form.name = name
        un_location_form.loc_code = code
        un_location_form.country_id = country_id
        return un_location_form.save()

    @classmethod
    def setup_cargo_type_data(cls):
        """
        Get recordset of cargo type from the data file for cargo.type
        """
        cls.fcl_sea_cargo_type = cls.env.ref('freight_base.cargo_type_sea_fcl')
        cls.lcl_sea_cargo_type = cls.env.ref('freight_base.cargo_type_sea_lcl')
        cls.lqd_sea_cargo_type = cls.env.ref('freight_base.cargo_type_sea_lqd')
        cls.courier_air_cargo_type = cls.env.ref('freight_base.cargo_type_air_courier')
        cls.ftl_land_cargo_type = cls.env.ref('freight_base.cargo_type_land_ftl')

    @classmethod
    def setup_incoterms_data(cls):
        """
        Get recordset of Incoterms from the data file for account.incoterms
        """
        cls.incoterm_EXW = cls.env.ref('account.incoterm_EXW')
        cls.incoterm_FCA = cls.env.ref('account.incoterm_FCA')
        cls.incoterm_FAS = cls.env.ref('account.incoterm_FAS')
        cls.incoterm_CFR = cls.env.ref('account.incoterm_CFR')
        cls.incoterm_DAP = cls.env.ref('account.incoterm_DAP')

    @classmethod
    def setup_house_shipment_data(cls, shipment_type, cargo_type, transport_mode, shipment_date, incoterm, **kwargs):
        """
        Create House Shipment record

        @param {recordset} shipment_type: record of 'shipment.type'
        @param {recordset} cargo_type: record of 'cargo.type'
        @param {recordset} transport_mode: record of 'transport.mode'
        @param {string} shipment_date: date of shipment
        @param {recordset} incoterm: record of 'account.incoterms'
        @returns {recordset}: record of 'freight.house.shipment'
        """
        house_shipment_form = Form(cls.env["freight.house.shipment"])
        house_shipment_form.shipment_date = shipment_date
        house_shipment_form.transport_mode_id = transport_mode
        house_shipment_form.shipment_type_id = shipment_type
        house_shipment_form.cargo_type_id = cargo_type
        house_shipment_form.inco_term_id = incoterm
        house_shipment_form.service_mode_id = cls.env.ref('freight_base.service_mode_d2p')
        house_shipment_form.client_id = cls.partner_client_id
        house_shipment_form.shipper_id = cls.partner_shipper_id
        house_shipment_form.consignee_id = cls.partner_consignee_id
        house_shipment_form.origin_un_location_id = cls.inmun_port_location
        house_shipment_form.destination_un_location_id = cls.aejea_port_location
        if kwargs.get('origin_port'):
            house_shipment_form.origin_port_un_location_id = kwargs.get('origin_port')
        if kwargs.get('destination_port'):
            house_shipment_form.destination_port_un_location_id = kwargs.get('destination_port')
        return house_shipment_form.save()

    @classmethod
    def setup_master_shipment_data(cls, shipment_type, cargo_type, transport_mode, shipment_date, **kwargs):
        """
        Create Master Shipment record

        @param {recordset} shipment_type: record of 'shipment.type'
        @param {recordset} cargo_type: record of 'cargo.type'
        @param {recordset} transport_mode: record of 'transport.mode'
        @param {string} shipment_date: date of shipment
        @returns {recordset}: record of 'freight.master.shipment'
        """
        master_shipment_form = Form(cls.env["freight.master.shipment"])
        master_shipment_form.shipment_date = shipment_date
        master_shipment_form.transport_mode_id = transport_mode
        master_shipment_form.shipment_type_id = shipment_type
        master_shipment_form.cargo_type_id = cargo_type
        master_shipment_form.service_mode_id = cls.env.ref('freight_base.service_mode_d2p')
        master_shipment_form.origin_un_location_id = cls.inmun_port_location
        master_shipment_form.origin_port_un_location_id = cls.inmun_origin_port
        master_shipment_form.destination_un_location_id = cls.aejea_port_location
        master_shipment_form.destination_port_un_location_id = cls.aejea_destination_port
        if kwargs.get('mbl_number'):
            master_shipment_form.carrier_booking_reference_number = kwargs.get('mbl_number')
        return master_shipment_form.save()

    @classmethod
    def setup_products(cls):
        """
        Get recordset of products from the data file for product.template
        """
        cls.delivery_product = cls.env.ref('freight_base.product_template_delivery')
        cls.pickup_product = cls.env.ref('freight_base.product_template_pickup')
        cls.on_carriage_product = cls.env.ref('freight_base.product_template_on_carriage')
        cls.pre_carriage_product = cls.env.ref('freight_base.product_template_pre_carriage')
        cls.main_carriage_product = cls.env.ref('freight_base.product_template_main_carriage')

    @classmethod
    def setup_container_category(cls):
        """
        Get recordset of Container Category from the data file for freight.container.category
        """
        cls.dry_storage_container = cls.env.ref('freight_base.cntr_type_dry_storage_container')
        cls.flat_rack_container = cls.env.ref('freight_base.cntr_type_flat_rack_container')

    @classmethod
    def setup_container_type(cls, name, code, teu_quantity, **kwargs):
        """
        Create record of freight.container.type (Container Type)

        @param {string} name
        @param {string} code
        @param {integer} teu_quantity
        @returns {recordset}: record of 'freight.container.type'
        """
        container_type_form = Form(cls.env["freight.container.type"])
        container_type_form.name = name
        container_type_form.code = code
        container_type_form.total_teu = teu_quantity
        if kwargs.get('container_category'):
            container_type_form.category_id = kwargs.get('container_category')
        return container_type_form.save()

    @classmethod
    def setup_partner_data(cls, name, **kwargs):
        """
        Create record of res.partner

        @param {string} name
        @returns {recordset}: record of 'res.partner'
        """
        partner_form = Form(cls.env["res.partner"])
        partner_form.name = name
        if kwargs.get('company_type'):
            partner_form.company_type = kwargs.get('company_type')
        partner_id = partner_form.save()

        # Add party types (Many2many field) in partner
        if kwargs.get('category_ids'):
            with Form(partner_id) as partner_form:
                for category in kwargs.get('category_ids'):
                    partner_form.category_ids.add(category)
        return partner_id

    @classmethod
    def setup_measurement_basis_data(cls):
        """
        Get recordset of Measurement Basis from the data file for freight.measurement.basis
        """
        cls.shipment_basis_measure = cls.env.ref('freight_base.measurement_basis_shipment')

    @classmethod
    def setup_freight_port_data(cls, name, code, country_ref, transport_mode, **kwargs):
        """
        Create record of freight.port (Ports)

        @param {string} name
        @param {string} code
        @param {string} country_ref
        @param {record} transport_mode
        @returns {recordset}: record of 'freight.port'
        """
        freight_port_obj = cls.env["freight.port"]
        port_id = freight_port_obj.search([('code', '=', code)])
        if port_id:
            return port_id
        port_form = Form(freight_port_obj)
        port_form.name = name
        port_form.code = code
        port_form.country_id = cls.setup_country_data(country_ref)
        port_form.transport_mode_id = transport_mode
        return port_form.save()

    def create_container(self, container_number, **kwargs):
        """
        Create Container.

        @param {string} container_number
        @return {recordset}: single record of 'freight.master.shipment.container.number'
        """
        container_id = self.env["freight.master.shipment.container.number"].search([('container_number', '=', container_number)], limit=1)
        if not container_id:
            container_form = Form(self.env["freight.master.shipment.container.number"])
            container_form.container_number = container_number
            return container_form.save()
        else:
            return container_id
