from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'

    sale_order_line_ids = fields.Many2many(
        'sale.order.line', 'sale_order_line_purchase_order_line_rel', 'pol_id', 'sol_id')
