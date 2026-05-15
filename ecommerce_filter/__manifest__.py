{
    'name': "Ecommerce Filter",

    'summary': """Desplazar las categorias del ecommerce a la izquierda
        """,

    'description': """Desplazar las categorias del ecommerce a la izquierda
    """,

    'author': "NextaDS",
    'website': "https://nextads.es/",

    'category': 'Ecommerce',
    'version': '19.0.0.8',
    'license': 'LGPL-3',

    'depends': ['base', 'website_sale', 'ecommerce_product'],

    'data': [
        'views/filmstrip_categories_category_views.xml',
        #'views/portrait_categories_views.xml',
        'views/attributes_views.xml',
        #'views/products_attributes_add_categories_views.xml',
        'views/filter_products_price.xml'
    ],
    # 'assets':{
    #     'web.assets_frontend':[
    #         'ecommerce_filter/static/src/scss/foundation.min.css',
    #         'ecommerce_filter/static/src/scss/style.css',
    #     ]
    # }
}
# -*- coding: utf-8 -*-
