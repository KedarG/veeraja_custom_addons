from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    option=fields.Float(string="Option")

class ProductTemplate(models.Model):
    _inherit="product.template"
    qbom_ids=fields.One2many('quotation.bom','product_tmpl_id')
    option=fields.Float(string="Option",compute="_compute_option",store=True,readonly=False)

    @api.depends('product_variant_ids', 'product_variant_ids.weight')
    def _compute_option(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.option = template.product_variant_ids.option
        for template in (self - unique_variants):
            template.option = 0.0
