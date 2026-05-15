# -*- coding: utf-8 -*-
{
    'name': "Ecommerce Product",

    'summary': """
        Muestra las características de los productos""",

    'description': """
         Muestra las características de los productos
    """,

    'author': "NextaDS",
    'website': "https://nextads.es/",

    'category': 'Ecommerce',
    'version': '19.0.2.1',
    'license': 'LGPL-3',

    'depends': ['base', 'website_sale', 'product', 'website', 'web',
                'stock','barcodes', 'web_studio', 'mrp',
                'account_accountant',
                'sale_product_pack', 'uom', 'website_payment', 'mrp_subcontracting', 'portal',
                'auth_signup'],

    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/odoo/product_template_form_view_custom.xml',
        'views/odoo/product_attribute_view_form_custom.xml',
        # 'views/odoo/product_template_only_form_view_custom.xml',
        'views/odoo/product_normal_form_view_custom.xml',
        'views/odoo/fiber_family_view.xml',
        'views/odoo/color_group_view.xml',
        'views/odoo/properties_view.xml',
        'views/odoo/usage_view.xml',
        'views/odoo/product_type_view.xml',
        'views/odoo/structure_view.xml',
        'views/odoo/care_instructions_view.xml',
        'views/odoo/certification_view.xml',
        'views/odoo/available_meters_view.xml',
        'views/odoo/composition_view.xml',
        'views/odoo/user_open_pack_view.xml',
        'views/odoo/open_pack_view.xml',
        'views/odoo/menuitem_product.xml',
        # 'views/website/product_custom.xml',
        # 'views/website/attributes_filter_view.xml',
        # 'views/website/footer_custom_custom.xml',
        # 'views/website/products_item_custom.xml',
        # 'views/website/products_custom.xml',
        # 'views/website/product_price_custom.xml',
        # 'views/website/dynamic_filter.xml',
        # 'views/website/product_details.xml',
        # 'views/website/variants_selector.xml',
        #'views/website/configure_optional_products_custom.xml',
        #'views/website/optional_product_items_custom.xml',
        # 'views/website/cart_lines_open_pack.xml',
        # 'views/website/cart_packs.xml',
        # 'views/website/product_alternatives_price.xml',
        'data/system_parameter.xml',
        # 'views/website/portal_templates.xml',
        # 'views/website/website_search_box_hide.xml',
        # 'views/website/auth_sign_login_templates.xml',
        # 'views/website/product_alternative.xml',
        #'views/website/website_sale_delivery.xml',
        'data/cron.xml'

    ],
    'demo': [
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap',
    #         'ecommerce_product/static/src/js/variant_mixin.js',
    #         #'ecommerce_product/static/src/js/product_configurator_modal.js'
    #     ]
    #     ,
    #     'web.assets_frontend': [
    #         'https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap',
    #         'ecommerce_product/static/src/scss/style.css',
    #         'ecommerce_product/static/src/scss/material.min.css',
    #         'ecommerce_product/static/src/js/material.min.js',
    #         'ecommerce_product/static/src/js/add_to_the_pack.js',
    #         'ecommerce_product/static/src/js/show_pack_price.js',
    #         'ecommerce_product/static/src/js/add_to_cart.js',
    #         # 'ecommerce_product/static/src/js/website_sale.js',
    #         'ecommerce_product/static/src/js/remove_from_cart.js',
    #         'ecommerce_product/static/src/js/variant_mixin.js',
    #         #'ecommerce_product/static/src/js/product_configurator_modal.js'
    #
    #     ]
    #
    # }
}
