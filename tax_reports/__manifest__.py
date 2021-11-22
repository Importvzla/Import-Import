# -*- coding: utf-8 -*-
{
    'name': "tax_reports",

    'summary': """
        Collection of tax reports""",

    'description': """
        Collection of tax reports
    """,

    'author': "Fabio Tamburini",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/paper_format.xml',
        'views/actions_report.xml',
        'views/res_partner.xml',
        'views/account_move.xml',
        'reports/islr_voucher.xml',
        'reports/iva_voucher.xml',
        'reports/iva_txt.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
