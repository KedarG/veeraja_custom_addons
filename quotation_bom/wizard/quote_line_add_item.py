from odoo import api, fields, models, _
from odoo.exceptions import UserError


class QuoteLineAddItem(models.TransientModel):
    _name = 'quoteline.additem'
    _description = 'Quote Line Add Item'

    product_id = fields.Many2one(
        'product.product', string="Product", help="Actual Product / Item ", required=True)
    product_qty = fields.Float(
        'Product Quantity', help="Quantity of the product", default=1.00)
    product_tmpl_id = fields.Many2one(
        'product.template', string="Product Template", default=lambda self: self.product_id.product_tmpl_id, help="The Product Template for which you will be selecting the Appropriate Variant")
    qbom_tmpl_id = fields.Many2one(
        'quotation.bom.line', string="Quotation BOM")
    bom_tmpl_id = fields.Many2one('mrp.bom', string="Engineering BOM")
    copy_from = fields.Selection(string='Copy From', selection=[(
        'qbom', 'Quotation BOM'), ('bom', 'Engineering BOM')])

    @api.multi
    def add_item(self):
        print('active Id', self.env.context['active_ids'])
        active_ids = self.env.context['active_ids']
        if len(active_ids) > 1:
            raise UserError(_("Please select one Product / Item "))
        for i in active_ids:
            qbom_line_obj = self.env['quotation.bom.line'].browse(i)

            vals = {
                "product_id": self.product_id.id,
                'name': self.product_id.name,
                "product_qty": self.product_qty,
                "product_tmpl_id": self.product_tmpl_id.id,
                "qbom_tmpl_id": self.qbom_tmpl_id.id,
                "bom_tmpl_id": self.bom_tmpl_id.id,
                "copy_from": self.copy_from,
                'level': str(int(qbom_line_obj.level)+1),
                'bom_parent_id': qbom_line_obj.id
            }
            qbom_line_obj.create(vals)

    @api.onchange('product_id')
    def find_bom(self):
        if self.product_id:
            li = []
            domain = {}
            prod_prod_obj = self.env['product.product'].browse(
                self.product_id.id)
            prod_tmpl_obj = self.env['product.template'].browse(
                prod_prod_obj.product_tmpl_id.id)
            bom_objs = self.env['mrp.bom'].search(
                [('product_tmpl_id', '=', prod_tmpl_obj.id), ('product_id', '=', prod_prod_obj.id)])
            if bom_objs:
                for prod in bom_objs:
                    li.append(prod.id)
                domain['bom_tmpl_id'] = [('id', 'in', li)]
                return {'domain': domain}
            else:
                domain['bom_tmpl_id'] = [('id', 'in', [])]
                return {'domain': domain}
        else:
            li = []
            domain = {}
            prod_tmpl_obj = self.env['product.template'].browse(
                self.product_tmpl_id.id)
            bom_objs = self.env['mrp.bom'].search(
                [('product_tmpl_id', '=', prod_tmpl_obj.id)])
            if bom_objs:
                for prod in bom_objs:
                    li.append(prod.id)
                domain['bom_tmpl_id'] = [('id', 'in', li)]
                return {'domain': domain}
            else:
                domain['bom_tmpl_id'] = [('id', 'in', [])]
                return {'domain': domain}

    @api.onchange('product_id')
    def find_qboms(self):
        if self.product_id:
            li = []
            domain = {}
            prod_prod_obj = self.env['product.product'].browse(
                self.product_id.id)
            prod_tmpl_obj = self.env['product.template'].browse(
                prod_prod_obj.product_tmpl_id.id)
            qbom_objs = self.env['quotation.bom.line'].search(
                ['&', ('product_tmpl_id', '=', prod_tmpl_obj.id), ('product_id', '=', prod_prod_obj.id)])
            if qbom_objs:
                for prod in qbom_objs:
                    li.append(prod.id)
                domain['qbom_tmpl_id'] = [('id', 'in', li)]
                return {'domain': domain}
            else:
                domain['qbom_tmpl_id'] = [('id', 'in', [])]
                return {'domain': domain}
        else:
            li = []
            domain = {}
            prod_tmpl_obj = self.env['product.template'].browse(
                self.product_tmpl_id.id)
            qbom_objs = self.env['quotation.bom.line'].search(
                [('product_tmpl_id', '=', prod_tmpl_obj.id)])
            if qbom_objs:
                for prod in qbom_objs:
                    li.append(prod.id)
                domain['qbom_template_id'] = [('id', 'in', li)]
                return {'domain': domain}
            else:
                domain['qbom_template_id'] = [('id', 'in', [])]
                return {'domain': domain}
