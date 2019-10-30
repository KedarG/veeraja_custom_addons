# -*- coding: utf-8 -*-
{
    'name': "Budget Without Manadatory Date to and Date from",
    'author': "Jeevan Gangarde",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_budget'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
'views/crossovered_budget_inherit.xml'
    ],
    # only loaded in demonstration mode
}
