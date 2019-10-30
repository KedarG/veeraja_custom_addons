from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = 'product.product'

    option = fields.Float(string="Option")
    moh = fields.Float(string="MOH(%)")
    boh = fields.Float(string="BOH(%)")
    # product_file = fields.Binary()
    # product_doc = fields.Binary(string="Product Document",attachment=True,store=True)
    # filename = fields.Char("filename",store=True)
    # presale_ids = fields.Many2many('res.users', 'presale_user', 'order_id', 'user_id', string='PreSales',domain=lambda self:self._display_presale_saleorder())
    lst_price = fields.Float(
        'Sale Price', compute='_compute_product_lst_price',default=1.0,
        digits=dp.get_precision('Product Price'), inverse='_set_product_lst_price',
        help="The sale price is managed from the product template. Click on the 'Variant Prices' button to set the extra attribute prices.")


class ProductTemplate(models.Model):
    _inherit = "product.template"
    product_file = fields.Binary(string="Upload Product File")
    filename = fields.Char("filename",store=True)
    qbom_ids = fields.One2many('quotation.bom', 'product_tmpl_id')
    option = fields.Float(
        string="Option", compute="_compute_option", store=True, readonly=False)
    moh = fields.Float(string="MOH(%)", compute="_compute_moh",
                       store=True, readonly=False)
    boh = fields.Float(string="BOH(%)", compute="_compute_boh",
                       store=True, readonly=False)
    product_doc = fields.Binary(string="Product Document",attachment=True)
    filename = fields.Char("filename")
    product_label = fields.Many2many('product.label','product_label_rel','product_id','label_id',string="Labels")
    type = fields.Selection(selection_add=[('product', 'Stockable Product')],default='product')
    @api.depends('product_variant_ids', 'product_variant_ids.boh')
    def _compute_boh(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.boh = template.product_variant_ids.boh
        for template in (self - unique_variants):
            template.boh = 0.0

    @api.depends('product_variant_ids', 'product_variant_ids.moh')
    def _compute_moh(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.moh = template.product_variant_ids.moh
        for template in (self - unique_variants):
            template.moh = 0.0

    @api.depends('product_variant_ids', 'product_variant_ids.option')
    def _compute_option(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.option = template.product_variant_ids.option
        for template in (self - unique_variants):
            template.option = 0.0
