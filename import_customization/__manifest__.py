# -*- coding: utf-8 -*-
{
    'name': "Import Customization",

    'summary': """
        Import Customization""",

    'description': """
        Import Customization
    """,

    'author': "Arkisoft / Fabio Tamburini",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'tax_report'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/invoice_paper_format.xml',
        'data/res_country.xml',
        'views/account_move.xml',
        'views/import_import_report.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        # 'views/sale_order_line.xml',
        'reports/import_import_bill.xml',
        'reports/import_invoice_ves.xml',
        'reports/import_invoice_usd.xml',
        'reports/report_invoice.xml',
        'reports/inc_invoice_usd.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
