from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrderSchedule(models.Model):
    _name = 'sale.order.schedule'
    _description = 'Sales Order Schedule'

    name = fields.Char(string='Name')
    product_id = fields.Many2one('product.product', required=True)
    product_uom = fields.Many2one('product.uom')
    order_line_id = fields.Many2one(
        'sale.order.line', string="Sale Order Item")
    ordered_qty = fields.Float(string="Ordered Quantity")

    def get_delivered_qty(self):
        for schedule in self:
            for picking in schedule.order_line_id.order_id.picking_ids:
                if picking and picking.picking_type_id.name == "Delivery Orders":
                    for move in picking.move_lines:
                        if move.product_id == schedule.product_id:
                            schedule.delivered_qty = move.quantity_done

    delivered_qty = fields.Float(
        string="Delivered Quantity", compute="get_delivered_qty", store=False)
    invoice_qty = fields.Float(string='Invoiced Quantity')
    scheduled_qty = fields.Float(string='Scheduled Quantity')
    scheduled_date = fields.Datetime(string='Scheduled Date')
    state = fields.Selection(string='', selection=[(
        'open', 'Open'), ('release', 'Release'), ('close', 'Close')],default='open')
    procurement_group_id = fields.Many2one('procurement.group')
    qty_release = fields.Float(string="Release Quantity", store=True)

    @api.multi
    def _get_qty_procurement(self):
        """
        Called in action_launch_procurement_rule to get the released quantity
        Changes by Jeevan Gangarde March 2019
        """
        for schedule_line in self:
            return schedule_line.scheduled_qty

    @api.onchange('product_id')
    def onchng_set_first_level_product(self):
        if self.product_id:
            bom = self.order_line_id.product_id.bom_ids.bom_line_ids.filtered(
                lambda m: m.product_id == self.product_id)
            qty = bom.product_qty * self.order_line_id.product_uom_qty
            uom = bom.product_uom_id
            self.ordered_qty = qty
            self.product_uom = uom
        else:
            domain = {}
            li = []
            for schedule in self:
                if schedule.order_line_id:
                    for i in self.order_line_id.product_id.bom_ids.bom_line_ids:
                        li.append(i.product_id.id)
                    domain['product_id'] = [('id', 'in', li)]
            return {'domain': domain}

    @api.constrains('scheduled_qty')
    def validate_scheduled_qty(self):
        scheduled_products = self.search([('order_line_id', '=', self.order_line_id.id)]).filtered(
            lambda m: m.product_id == self.product_id)
        print("scheduled_products", scheduled_products)
        total_qty = 0.0
        for product in scheduled_products:
            total_qty += product.scheduled_qty

        if total_qty < self.scheduled_qty:
            raise UserError(
                _("Scheduled Quantity Can not be more than the Ordered Quantity"))
