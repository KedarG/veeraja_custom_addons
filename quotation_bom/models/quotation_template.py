from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class SaleQuoteLine(models.Model):
    _inherit = 'sale.quote.line'

    product_tmpl_id = fields.Many2one('product.template', string='Product Template',change_default=True, ondelete='restrict', required=True)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    product_category_id=fields.Many2one("product.category",string='Part')
