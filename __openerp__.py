# -*- coding: utf-8 -*-
{
    'name': "Commandes de sirop d'érable",

    'summary': """
	Commande de sirop aux producteurs
	""",

    'description': """
        Permet de créer et de suivre les commandes de sirop d'érable
    """,

    'author': "Global Technologie",
    'website': "http://www.globaltechnologie.ca",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','stock','product'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/reports.xml',
		'security/user_groups.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
