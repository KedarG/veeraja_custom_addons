from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'

    purchase_line_ids = fields.Many2many(
        'purchase.order.line', 'sale_order_line_purchase_order_line_rel', 'sol_id', 'pol_id')
