# -*- coding: utf-8 -*-
{
    'name': "Purchase Analytic Account",

    'summary': """
        Add analytic account to purchase and purchase report""",

    'description': """
         Add analytic account to purchase and purchase report
    """,

    'author': "NextaDS",
    'website': "https://nextads.es/",

    'category': 'Sale',
    'version': '19.0.0.1',
    'license': 'LGPL-3',

    'depends': [
        'purchase',
        'account',
    ],

    'data': [
        'views/purchase_order.xml',
    ],
}
