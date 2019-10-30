# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # @api.onchange('order_line.price_unit')
    # def unit_price_validation(self):
    #     for line in self.order_line:
    #         sale_obj = self.env['sale.order'].search(
    #             [('name', '=', self.origin)])
    #         if sale_obj and sale_obj.order_line:
    #             for i in sale_obj.order_line:
    #                 if i.qbom_ids:
    #                     for qbom_line in i.qbom_lines:
    #                         if qbom_line.product_id.id == line.product_id.id:
    #                             if line.price_unit > i.budget:
    #                                 raise UserError(
    #                                     _('The Budget specified id less than the Cost for Item'+line.product_id.name))
    # @api.multi
    # def button_confirm(self):
    #     super(PurchaseOrder, self).button_confirm()
    #     for order in self:
    #         if self.origin:
    #             sale_obj = self.env['sale.order'].search(
    #                 [('name', '=', self.origin)])
    #         if order.order_line:
    #             for line in order.order_line:
    #                 if line.price_unit:
    #                     if sale_obj:
    #                         for i in sale_obj.order_line:
    #                             if i.qbom_ids:
    #                                 for qbom in i.qbom_ids:
    #                                     if qbom.qbom_lines:
    #                                         for qbom_line in qbom.qbom_lines:
    #                                             if qbom_line.product_id.id == line.product_id.id:
    #                                                 if line.price_unit > qbom_line.budget:
    #                                                     raise UserError(
    #                                                         _('The Budget specified id less than the Cost for Item'))


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    account_analytic_id = fields.Many2one(
        'account.analytic.account', compute="set_account_analytic_id", store=True, readonly=False)

    @api.depends('order_id.origin')
    def set_account_analytic_id(self):
        sale_obj = self.env['sale.order'].search(
            [('name', '=', self.order_id.origin)])
        if sale_obj:
            # for line in self.order_line:
            self.account_analytic_id = sale_obj.analytic_account_id.id

    @api.onchange('price_unit')
    def unit_price_validation(self):
        for line in self:
            if line.price_unit:
                if self.order_id.origin:
                    sale_obj = self.env['sale.order'].search(
                        [('name', '=', self.order_id.origin)])
                    if sale_obj:
                        for i in sale_obj.order_line:
                            if i.qbom_ids:
                                for qbom in i.qbom_ids:
                                    if qbom.qbom_lines:
                                        for qbom_line in qbom.qbom_lines:
                                            if qbom_line.product_id.id == line.product_id.id:
                                                # val = 0.0
                                                # val = line.price_unit*line.product_qty
                                                if line.price_subtotal > qbom_line.budget:
                                                    raise UserError(
                                                        _('The Budget specified id less than the Cost for Item'))
