# from odoo import api, fields, models


# class PurchaseOrderWizard(models.TransientModel):
#     _inherit = 'purchase.order.wizard'

#     def create_purchase_order(self):
#         active_ids = self.env.context['active_ids']
#         for active_id in active_ids:
#             sale_order_id = self.env['sale.order'].browse(active_id)
#             if sale_order_id.order_line:
#                 for line in sale_order_id.order_line:
#                     if line.product_id.virtual_available <0 or :
