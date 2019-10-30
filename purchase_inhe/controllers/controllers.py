# -*- coding: utf-8 -*-
from odoo import http

# class PurchaseInhe(http.Controller):
#     @http.route('/purchase_inhe/purchase_inhe/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_inhe/purchase_inhe/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_inhe.listing', {
#             'root': '/purchase_inhe/purchase_inhe',
#             'objects': http.request.env['purchase_inhe.purchase_inhe'].search([]),
#         })

#     @http.route('/purchase_inhe/purchase_inhe/objects/<model("purchase_inhe.purchase_inhe"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_inhe.object', {
#             'object': obj
#         })