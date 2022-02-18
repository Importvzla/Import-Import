# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'All in one Split -Sale, Purchase, Stock',
    'version': '14.0.1.0',
	'licence': 'Other proprietary',
    'sequence': 1,
    'category': 'Sales',
    'description':
        """
This Module add below functionality into odoo

        1.Create separate sale order for selected lines of selected sale order

        2.Create separate purchase order for selected lines of selected purchase order

        3.Create separate picking order for selected lines of selected picking

split sales orders | Split purchases orders | Split stock operation | split-sale order | split purchase order | split delivery order | split order | split quotation | Split sale | split purchase | split delivery | split shipment | split inventory | split picking | split RFQ | split quotation


    """,
    'summary': 'split sales orders | Split purchases orders | Split stock operation | split-sale order | split purchase order | split delivery order | split order | split quotation | Split sale | split purchase | split delivery | split shipment | split inventory | split picking | split RFQ | split quotation',
    'depends': ['sale_management', 'purchase', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/dev_split_sale_view.xml',
        'wizard/split_sale_order_view.xml',
        'views/dev_split_purchase_view.xml',
        'wizard/split_purchase_order_view.xml',
        'views/dev_split_picking_view.xml',
        'wizard/split_picking_view.xml',
        ],
	'demo': [],
	'test': [],
	'css': [],
	'qweb': [],
	'js': [],
	'images': [
		'images/main_screenshot.png'],
	'installable': True, 
	'application': True, 
	'auto_install': False, 
	#========= Author and Support Details =========#
	'author': 'DevIntelle Consulting Service Pvt.Ltd', 
	'website': 'http://www.devintellecs.com', 
	'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
	'support': 'devintelle@gmail.com', 
	'price': 22.0, 
	'currency': 'EUR', 
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
