# -*- coding: utf-8 -*-
# from odoo import http


# class TaxReports(http.Controller):
#     @http.route('/tax_reports/tax_reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tax_reports/tax_reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tax_reports.listing', {
#             'root': '/tax_reports/tax_reports',
#             'objects': http.request.env['tax_reports.tax_reports'].search([]),
#         })

#     @http.route('/tax_reports/tax_reports/objects/<model("tax_reports.tax_reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tax_reports.object', {
#             'object': obj
#         })
