from odoo import api, fields, models


class ProductLabel(models.Model):
    _name = 'product.label'
    _rec_name='label'
    label = fields.Char("Label")


    prod_ids = fields.Many2many(
        'product.template', 'product_label_rel', 'label_id', 'product_id')