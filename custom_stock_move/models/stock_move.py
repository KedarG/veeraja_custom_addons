# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class stock_move(models.Model):
    _inherit = 'stock.move'

    product_qty = fields.Float(
        'Real Quantity', compute='_compute_product_qty', inverse='_set_product_qty',
        digits=dp.get_precision('Product Unit of Measure'), store=True,
        help='Quantity in the default UoM of the product')


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_qty = fields.Float(
        'Real Reserved Quantity', digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_product_qty', inverse='_set_product_qty', store=True)
