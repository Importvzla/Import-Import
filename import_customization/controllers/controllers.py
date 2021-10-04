# -*- coding: utf-8 -*-
# from odoo import http


# class ImportCustomization(http.Controller):
#     @http.route('/import_customization/import_customization/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/import_customization/import_customization/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('import_customization.listing', {
#             'root': '/import_customization/import_customization',
#             'objects': http.request.env['import_customization.import_customization'].search([]),
#         })

#     @http.route('/import_customization/import_customization/objects/<model("import_customization.import_customization"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('import_customization.object', {
#             'object': obj
#         })
