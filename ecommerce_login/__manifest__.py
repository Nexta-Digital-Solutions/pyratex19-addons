# -*- coding: utf-8 -*-
{
    'name': "Ecommerce Login",

    'summary': """
        Modificaciones en el login para el acceso y configuración de MNDA.
        """,

    'description': """
        Modificaciones en el login para el acceso y configuración de MNDA.
    """,

    'author': "NextaDS",
    'website': "https://nextads.es/",

    'category': 'Ecommerce',
    'version': '19.0.1.2',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'auth_signup',
        'website',
        'website_sale',
        'documents',
        'documents_account'
    ],
    'external_dependencies': {
        'python': ['python-docx', 'docxtpl'],
    },

    'data': [
        'views/complete_your_profile.xml',
        'views/billing_address.xml',
        #'views/signup_custom.xml',
        'views/mlnda.xml',
        'views/process_complete.xml',
        'views/loader.xml',
        'views/res_country_website.xml',
        'views/res_partner.xml'
    ],
    
    'assets': {
        'web.assets_frontend': [
            # Odoo 19: Vue 2, jQuery.serializeJSON y vue_instance.js ya no son necesarios
            'ecommerce_login/static/src/interactions/complete_profile.js',
            'ecommerce_login/static/src/scss/signature.scss',
            'ecommerce_login/static/src/scss/loader.scss',
        ],
    },
    'post_init_hook': 'post_init_hook',
}
