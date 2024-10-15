# -*- coding: utf-8 -*-

def migrate(cr, version):
    '''Data file moved from freight_management to freight_base: Update XML ID for data file record of charges-product'''

    products = (
        'product_template_pickup',
        'product_template_delivery',
        'product_template_on_carriage',
        'product_template_pre_carriage',
        'product_template_main_carriage'
    )

    query = "UPDATE ir_model_data SET module='freight_base' WHERE model='product.template' AND module='freight_management' AND name IN {}".format(products)
    cr.execute(query)
