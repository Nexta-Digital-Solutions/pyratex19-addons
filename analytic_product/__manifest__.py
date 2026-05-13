# -*- coding: utf-8 -*-
{
    'name': "Analytic Product",

    'summary': """
        Analytics for Products""",

    'description': """
         Analytics for Products
    """,

    'author': "NextaDS",
    'website': "https://nextads.es/",

    'category': 'Accounting',
    'version': '19.0.1.1',
    'license': 'LGPL-3',

    'depends': [
        'purchase',
        'sale_management',
        'account',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/product_template_analytic.xml',
        'data/cron.xml',
    ],
}
