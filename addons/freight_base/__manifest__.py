# -*- coding: utf-8 -*-
{
    'name': 'Freight Base',
    'version': '0.0.8',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Freight,CRM',
    'summary': 'Freight Base',
    'license': 'Other proprietary',
    'description': """
Freight Base
    """,
    'depends': [
        'odoo_base',
        'uom',
        'ics_account',
        'base_address_city',
        'product',
        'contacts',
        'base_document_reports',
        'phone_validation',
        'ics_base_import',
        'fetchmail',
        'base_iban',
        'web_domain_field',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/res_country.xml',
        'data/transport_mode_data.xml',
        'data/shipment_type_data.xml',
        'data/container_type_size_data.xml',
        'data/cargo_type_air_data.xml',
        'data/cargo_type_sea_data.xml',
        'data/cargo_type_land_data.xml',
        'data/consolidation_type_data.xml',
        'data/uom_category_data.xml',
        'data/res_users_data.xml',
        'data/measurement_basis_data.xml',
        'data/freight_base_data.xml',
        'data/freight_adjustment_ratio_type_data.xml',
        'data/freight.service.mode.csv',
        'data/container.service.mode.csv',
        'data/res.partner.type.csv',
        'data/res.partner.type.field.csv',
        'data/uom.uom.csv',
        'data/haz.sub.class.code.csv',
        'data/haz.sub.class.csv',
        'data/freight.container.category.csv',
        'data/account_incoterm_data.xml',
        'data/package.info.csv',
        'data/custom_master_be_type_data.xml',
        'data/decimal_precision_data.xml',
        'views/menu_data.xml',
        'views/freight_product_views.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_user_views.xml',
        'views/res_country_views.xml',
        'views/harmonized_system_code_views.xml',
        'views/container_category_views.xml',
        'views/container_type_views.xml',
        'views/transport_mode_views.xml',
        'views/uom_category_view.xml',
        'views/shipment_type_views.xml',
        'views/cargo_type_views.xml',
        'views/consolidation_type_views.xml',
        'views/service_mode_views.xml',
        'views/container_service_mode_views.xml',
        'views/freight_carrier_views.xml',
        'views/freight_un_location_views.xml',
        'views/freight_commodity_views.xml',
        'views/freight_port_views.xml',
        'views/freight_vessel_views.xml',
        'views/freight_vessel_category_views.xml',
        'views/contract_views.xml',
        'views/res_partner_views.xml',
        'views/freight_custom_location_views.xml',
        'views/freight_event_type.xml',
        'views/product_views.xml',
        'views/contacts_views.xml',
        'views/freight_document_type_views.xml',
        'views/res_partner_type_views.xml',
        'views/res_group_views.xml',
        'views/mail_server_views.xml',
        'views/freight_warehouse_depot_views.xml',
        'views/ir_mail_server_views.xml',
        'views/fetchmail_server_views.xml',
        'views/doc_version_history.xml',
        'views/freight_adjustment_ratio_type_views.xml',
        'views/freight_measurement_basis_views.xml',
        'views/language_menu_views.xml',
        'views/freight_sequence_views.xml',
        'views/freight_shipment_tag_view.xml',
        'views/res_bank_view.xml',
        'views/haz_sub_class_code_view.xml',
        'views/haz_sub_class_view.xml',
        'views/package_info_view.xml',
        'views/account_incoterms_views.xml',
        'views/custom_master_be_type_views.xml',
        'views/volumetric_divided_value.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'freight_base/static/src/js/partner_form_view.js',
        ],
    },
    'installable': True,
    'application': False,
}
