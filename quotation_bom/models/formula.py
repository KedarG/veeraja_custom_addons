# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Formula(models.Model):
    _name = 'formula.info'
    reference = fields.Char("Internal Reference ",
                            placeholder="Internal Reference")
    formula_line_id = fields.One2many("formula.details", 'formula_id')
    product_category_id = fields.Many2one(
        "product.category", string="Product Category")
    excel_formula = fields.Binary(string="Excel Formula", attachment=True)
    filename = fields.Char()
    excel_sheet_name = fields.Char(string="Excel Sheet Name")
    # This function overrides _rec_name
    @api.multi
    def name_get(self):
        res = []
        reference = ""
        for order in self:
            if order.product_category_id:
                name = order.product_category_id.complete_name
            if order.reference:
                reference = order.reference
            else:
                reference = ""
            res.append((order.id, reference+' '+name))
        return res


class FormulaDetail(models.Model):
    _name = 'formula.details'

    formula_id = fields.Many2one("formula.info")
    name = fields.Char("Name")
    parameter_name = fields.Char("Parameter")
    uom = fields.Char("UOM")
    formula_expression = fields.Char("Formula Expression")
    detail_product_category_id = fields.Many2one(
        "product.category", string="Product Category")
    process = fields.Selection(
        string="Process", selection=[("Input", "Input"), ("Output", "Output")]
    )
