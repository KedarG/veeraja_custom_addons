# -*- coding: utf-8 -*-
from odoo import http

# class CustomStockMove(http.Controller):
#     @http.route('/custom_stock_move/custom_stock_move/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_stock_move/custom_stock_move/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_stock_move.listing', {
#             'root': '/custom_stock_move/custom_stock_move',
#             'objects': http.request.env['custom_stock_move.custom_stock_move'].search([]),
#         })

#     @http.route('/custom_stock_move/custom_stock_move/objects/<model("custom_stock_move.custom_stock_move"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_stock_move.object', {
#             'object': obj
#         })