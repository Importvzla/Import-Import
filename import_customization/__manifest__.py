# -*- coding: utf-8 -*-
{
    'name': "import_customization",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Fabio Tamburini",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'base_report_to_printer', 'tax_report'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/invoice_paper_format.xml',
        'data/res_country.xml',
        'views/account_move.xml',
        'views/import_import_report.xml',
        'views/res_partner_views.xml',
        # 'views/sale_order_line.xml',
        'reports/import_import_bill.xml',
        # 'reports/budget_official_rate.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
