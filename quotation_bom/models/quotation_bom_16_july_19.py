from odoo import api, fields, models, _
from odoo.exceptions import UserError
import os
# import docx2txt
#import docx
import base64
import codecs
import io


class QuotationBom(models.Model):
    _name = 'quotation.bom'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Quotation BOM'

    name = fields.Char(
        string='Name', default=lambda self: _('New'), store=True)
    order_line_id = fields.Many2one(
        'sale.order.line', string="Sale Order Line")
    product_id = fields.Many2one('product.product',domain="['&', ('product_tmpl_id', '=', product_tmpl_id), ('type', 'in', ['product', 'consu'])]")
    product_tmpl_id = fields.Many2one('product.template')
    product_uom_qty = fields.Float(string='Quantity',default="1.0")
    product_uom_id = fields.Many2one('product.uom',default=lambda self: self.env['product.uom'].search([('name','=','Unit(s)')]))
    product_category_id = fields.Many2one('product.category',string='Product Category')
    description = fields.Text(string="Description", related='order_line_id.name',
                              required=True, store=True, help="Description of the Product")
    order_id = fields.Many2one(related='order_line_id.order_id', store=True)
    partner_id = fields.Many2one(
        related='order_id.partner_id', string='Customer')

    active = fields.Boolean(
        'Active', default=True,
        help="If the active field is set to False, it will allow you to hide the bills of material without removing it.")
    company_id = fields.Many2one(related='order_line_id.company_id')
    currency_id = fields.Many2one(
        "res.currency", related='order_line_id.currency_id', string="Currency", readonly=True, store="True")
    total_weight = fields.Float(
        string="Total Weight", store=True, compute='set_total_weight')
    total = fields.Monetary(string="Amount Total",
                            readonly=True, store=True, compute='_amount_all')
    manufacture_oh = fields.Float(string="Manfacture Over Head")
    bo_oh = fields.Float(string="BO Over Head")
    margin = fields.Float(string="Margin")
    copy_from = fields.Selection(string='Copy From', selection=[(
        'qbom', 'Quotation BOM'), ('bom', 'Engineering BOM')])
    
    level=fields.Char(default='0')
    saleline_category=fields.Many2one('product.category',string="Sale Line Solution Category", store=True,readonly=False)
    saleline_product_tmpl_id=fields.Many2one('product.template', string="Sale Line Solution",store=True,readonly=False)
    saleline_product_id=fields.Many2one('product.product',string="Sale Line Variant",store=True,readonly=False)   
    product_label = fields.Many2many(
        'product.label', 'product_label_quotation_bom_rel', 'qbom_id', 'label_id', string="Labels")
    logic_selection=fields.Selection([('and','AND'),('or','OR')],string="Labels AND / OR")
    #Method to set Quotation BOM to the Drop Down related to the Prod template or both prod tmpl and prod prod
    def set_quotation_template(self):
        '''
            Method to set Quotation Bom 
            based on the Product Template
        '''
        if 'default_order_line_id' in self.env.context:
            sol = self.env.context['default_order_line_id']
            sol_obj = self.env['sale.order.line'].browse(sol)
            if sol_obj.product_id and sol_obj.product_tmpl_id:
                li = []
                domain = {}
                prod_prod_obj = self.env['product.product'].browse(
                    sol_obj.product_id.id)
                prod_tmpl_obj = self.env['product.template'].browse(
                    prod_prod_obj.product_tmpl_id.id)
                qbom_objs = self.env['quotation.bom'].search(
                    [('product_tmpl_id', '=', prod_tmpl_obj.id), ('product_id', '=', prod_prod_obj.id)])
                if qbom_objs:
                    for prod in qbom_objs:
                        li.append(prod.id)
                    domain['qbom_template_id'] = [('id', 'in', li)]
                    return [('id', 'in', li)]
                else:
                    domain['qbom_template_id'] = [('id', 'in', [])]
                    return [('id', 'in', [])]
            else:
                li = []
                domain = {}
                prod_tmpl_obj = self.env['product.template'].browse(
                    sol_obj.product_tmpl_id.id).qbom_ids
                if prod_tmpl_obj:
                    for prod in prod_tmpl_obj:
                        li.append(prod.id)
                    domain['qbom_template_id'] = [('id', 'in', li)]
                    return [('id', 'in', li)]
                else:
                    domain['qbom_template_id'] = [('id', 'in', [])]
                    return [('id', 'in', [])]
    qbom_template_id = fields.Many2one(
        'quotation.bom', string='Quotation BOM')#, domain=lambda self: self.set_quotation_template())
    #Method to set MRP BOM to the Drop Down related to the Prod template or both prod tmpl and prod prod
    def set_bom_template(self):
        '''
            Method to set Engineering Bom 
            based on the Product Template
        '''
        if 'default_order_line_id' in self.env.context:
            sol = self.env.context['default_order_line_id']
            sol_obj = self.env['sale.order.line'].browse(sol)
            if sol_obj.product_id and sol_obj.product_tmpl_id:
                li = []
                domain = {}
                prod_prod_obj = self.env['product.product'].browse(
                    sol_obj.product_id.id)
                prod_tmpl_obj = self.env['product.template'].browse(
                    prod_prod_obj.product_tmpl_id.id)
                qbom_objs = self.env['mrp.bom'].search(
                    [('product_tmpl_id', '=', prod_tmpl_obj.id), ('product_id', '=', prod_prod_obj.id)])
                if qbom_objs:
                    for prod in qbom_objs:
                        li.append(prod.id)
                    domain['bom_template_id'] = [('id', 'in', li)]
                    return [('id', 'in', li)]
                else:
                    domain['bom_template_id'] = [('id', 'in', li)]
                    return [('id','in',[])]
            else:
                li = []
                domain = {}
                prod_tmpl_obj = self.env['product.template'].browse(
                    sol_obj.product_tmpl_id.id)
                qbom_objs = self.env['mrp.bom'].search(
                    [('product_tmpl_id', '=', prod_tmpl_obj.id)])
                if qbom_objs:
                    for prod in qbom_objs:
                        li.append(prod.id)
                    domain['bom_template_id'] = [('id', 'in', li)]
                    return [('id', 'in', li)]
                else:
                    domain['bom_template_id'] = [('id', 'in', li)]
                    return [('id','in',[])]
    bom_template_id = fields.Many2one(
        'mrp.bom', string='Engineering BOM')#, domain=lambda self: self.set_bom_template())
    qbom_lines = fields.One2many("quotation.bom.line",'qbom_id')
    #Method to set Total weight
    @api.depends('qbom_lines.weight')
    def set_total_weight(self):
        for order in self:
            if order.qbom_lines:
                weight_tot = 0
                for i in order.qbom_lines:
                    if i.level == "0":
                        weight_tot += i.weight or 0.0
                order.total_weight = weight_tot

    def context_values(self):
        #qbom_detail = self.env['quotation.bom.line']
        li2=[]
        for order in self:
            for i in order.qbom_template_id.qbom_lines:
                values = {
                    "name":i.name or i.product_id.name or i.product_tmpl_id.name or i.product_category_id.name,
                    "product_id":i.product_id,
                    'product_tmpl_id':i.product_tmpl_id,
                    'product_qty':i.product_qty,
                    'product_uom_id':i.product_uom_id,
                    'product_category_id':i.product_category_id,
                    'purchase_price':i.purchase_price,
                    'new_price_unit':i.new_price_unit,
                    'manufacture_oh':i.manufacture_oh,
                    'bo_oh':i.bo_oh,
                    'price_subtotal':i.price_subtotal,
                    'margin':i.margin,
                    'level':i.level,
                    'immi_parent_id':i.immi_parent_id,
                    'product_orig_qty':i.product_orig_qty if i.product_orig_qty else i.product_qty/i.qbom_id.product_uom_qty
                }
                li2.append((0,0,values))
                #print("@@@@@@@@###############=============>",li2)
        return li2
        # for z in li2:
        #     values={
        #             "name": z[2]['name'],
        #             "product_id": z[2]['product_id'].id,
        #             "product_tmpl_id": z[2]['product_tmpl_id'].id,
        #             "product_qty": z[2]['product_qty'],
        #             "product_uom_id": z[2]['product_uom_id'].id,
        #             "product_category_id": z[2]['product_category_id'].id,
        #             "purchase_price": z[2]['purchase_price'],
        #             "new_price_unit": z[2]['new_price_unit'],
        #             "level": z[2]['level'],
        #             'immi_parent_id': z[2]['immi_parent_id'].id,
        #             #'qbom_id':order.qbom_id.id
        #     }
        # return values
        # .search(
        #     [('qbom_id', '=', self.qbom_template_id.id)])
        # li = []
        # for order in qbom_detail:
        #     values = {
        #         "name": order.name or order.product_id.name or order.product_tmpl_id.name or order.product_category_id.name,
        #         "product_id": order.product_id,
        #         'product_tmpl_id': order.product_tmpl_id,
        #         'product_qty': order.product_qty,
        #         'product_uom_id': order.product_uom_id,
        #         'product_category_id': order.product_category_id,
        #         'purchase_price': order.purchase_price,
        #         'new_price_unit': order.new_price_unit,
        #         'manufacture_oh': order.manufacture_oh,
        #         'bo_oh': order.bo_oh,
        #         'price_subtotal': order.price_subtotal,
        #         'margin': order.margin,
        #         'level':'0',
        #         'immi_parent_id':self.product_id
        #     }
        #     li.append((0, 0, values))
        #     for i in order.transaction_lines:
        #             for j in i.product_ids:
        #                 new_values = {
        #                     'product_id': j.product_id,
        #                     'name': j.description,
        #                     'price_subtotal': j.cost,
        #                     'immi_parent_id': order.product_id,
        #                     'level': '1',
        #                 }
        #                 li.append((0,0,new_values))
        # return li

    @api.onchange('qbom_template_id')
    def get_record_db(self):
        if self.qbom_template_id:
            self.context_values()
            self.qbom_lines = [j for j in self.context_values()]

    @api.model
    def _get_child_vals(self, record, level, qty, uom):
        child = {
            "name": record.product_id.name or record.product_id.product_tmpl_id.name or record.product_id.product_tmpl_id.categ_id.name,
            "product_id": record.product_id,
            "product_tmpl_id": record.product_id.product_tmpl_id,
            "product_qty": record.product_qty,
            "product_uom_id": record.product_uom_id,
            "product_category_id": record.product_id.product_tmpl_id.categ_id,
            "purchase_price": record.product_id.standard_price,
            "new_price_unit": record.product_id.lst_price,
            "level": level,
            'immi_parent_id': record.bom_id.product_id,
            'product_orig_qty': record.product_qty
        }
        qty_per_bom = record.bom_id.product_qty
        if uom:
            if uom != record.bom_id.product_uom_id:
                qty = uom._compute_quantity(qty, record.bom_id.product_uom_id)
            child['product_qty'] = (record.product_qty * qty) / qty_per_bom
        else:
            child['product_qty'] = (record.product_qty * qty)
        return child

    def get_children(self, records, level=0,qty=1.0):
        result = []
        
        def _get_rec(records, level, qty=1.0, uom=False):
            for l in records:
                child = self._get_child_vals(l, level, qty, uom)
                result.append((0, 0, child))
                if l.child_line_ids:
                    level += 1
                    _get_rec(l.child_line_ids, level,
                             qty=child['product_qty'], uom=child['product_uom_id'])
                    if level > 0:
                        level -= 1
            return result

        children = _get_rec(records, level,qty=qty)

        return children

    def bom_context_values(self):
        li1 = self.get_children(self.bom_template_id.bom_line_ids,qty=self.product_uom_qty)
        return li1

    @api.onchange('bom_template_id')
    def get_bom_details(self):
        if self.bom_template_id:
            self.qbom_lines = [j for j in self.bom_context_values()]
           
    @api.onchange('margin')
    def onchng_margin(self):
        if self.margin:
            for qbom in self:
                if qbom.qbom_lines:
                    for qbom_line in qbom.qbom_lines:
                        qbom_line.margin = qbom.margin

    @api.onchange('manufacture_oh')
    def onchng_manufacture_oh(self):
        if self.manufacture_oh:
            for qbom in self:
                if qbom.qbom_lines:
                    for qbom_line in qbom.qbom_lines:
                        qbom_line.manufacture_oh = qbom.manufacture_oh

    @api.onchange('bo_oh')
    def onchng_bo_oh(self):
        if self.bo_oh:
            for qbom in self:
                if qbom.qbom_lines:
                    for qbom_line in qbom.qbom_lines:
                        qbom_line.bo_oh = qbom.bo_oh

    @api.depends('qbom_lines.price_subtotal')
    def _amount_all(self):
        for order in self:
            amt_total = 0
            for line in order.qbom_lines:
                if line.level=='0':
                    amt_total += line.price_subtotal
            order.update({
                'total': amt_total
            })
    @api.onchange('product_id')
    def set_qbom(self):
        li=[]
        domain={}
        if self.product_id:
            qbom_objs = self.env['quotation.bom'].search([('product_id', '=',self.product_id.id)])
            if qbom_objs:
                for prod in qbom_objs:
                    li.append(prod.id)
                domain['qbom_template_id'] = [('id', 'in', li)]
                return {'domain':domain}
            else:
                domain['qbom_template_id'] = [('id', 'in', [])]
                return {'domain':domain}
        else:
            qbom_objs = self.env['quotation.bom'].search([('product_tmpl_id', '=', self.product_tmpl_id.id)])
            if qbom_objs:
                for prod in qbom_objs:
                    li.append(prod.id)
                domain['qbom_template_id'] = [('id', 'in', li)]
                return {'domain':domain}
            else:
                domain['qbom_template_id'] = [('id', 'in', [])]
                return {'domain':domain}
        # else:
        #     qbom_objs = self.env['quotation.bom'].search([('product_tmpl_id', '=', self.product_tmpl_id.id)])
        #     if qbom_objs:
        #         for prod in qbom_objs:
        #             li.append(prod.id)
        #         domain['qbom_template_id'] = [('id', 'in', li)]
        #         return {'domain':domain}
        #     else:
        #         domain['qbom_template_id'] = [('id', 'in', [])]
        #         return {'domain':domain}

    @api.onchange('product_id')
    def set_bom(self):
        il=[]
        domain={}
        if self.product_id:
            bom_objs=self.env['mrp.bom'].search([('product_id','=',self.product_id.id)])
            if bom_objs:
                for bom in bom_objs:
                    il.append(bom.id)
                domain['bom_template_id']=[('id','in',il)]
                return {'domain':domain}
            else:
                domain['bom_template_id'] = [('id', 'in', [])]
                return {'domain':domain}
        # else:
        #     domain['bom_template_id'] = [('id', 'in', [])]
        #     return {'domain':domain}
        # else:
        #     bom_objs=self.env['mrp.bom'].search([('product_tmpl_id','=',self.product_tmpl_id.id)])
        #     if bom_objs:
        #         for bom in bom_objs:
        #             il.append(bom.id)
        #         domain['bom_template_id']=[('id','in',il)]
        #         return {'domain':domain}
        #     else:
        #         domain['bom_template_id'] = [('id', 'in', [])]
        #         return {'domain':domain}
    @api.model
    def create(self, vals):
        prod_id = self.env['product.product'].browse(vals['product_id'])
        sol_id=self.env['sale.order.line'].browse(vals['order_line_id'])
        if vals:
            vals['name']=sol_id.order_id.name
            vals['name'] += '-'+self.env['ir.sequence'].next_by_code(
                "quotation.bom")
            vals['name'] += '-'+ prod_id.name if prod_id else '--'+vals['description']
        new_id = super(QuotationBom, self).create(vals)
        # for order in new_id:
        #     for i in order.qbom_lines:
        #         if i.level != '0':
        #             par_ids = i.env['quotation.bom.line'].search(
        #                 [('qbom_id', '=', order.id), ('product_id', '=', i.immi_parent_id.id)])
        #             if par_ids:
        #                 for j in par_ids:
        #                     i.bom_parent_id = j.id
        return new_id
   

    @api.multi 
    def write(self,vals):
        if vals:
            if 'product_uom_qty' in vals:
                for order in self:
                    for i in order.qbom_lines:
                        if i.level=='0':
                            i.product_qty=vals['product_uom_qty']*i.product_orig_qty
        new_id = super(QuotationBom, self).write(vals)
        return new_id
    #Created by Ajinkya on  24/06/2019
    @api.onchange('product_category_id')
    def onchng_set_prod_template(self):
        for line in self:
            li = []
            domain = {}
            if 'default_product_category_id' in self.env.context:
                if self.env.context['default_product_category_id']:
                    line.product_id = False 
                    #print("Default Category id ",self.env.context['default_product_category_id'])
                    prod_tmpls = line.env['product.product'].search(
                        [('categ_id', '=', self.env.context['default_product_category_id'])])
                    #print("Prod Temps",prod_tmpls)
                    if prod_tmpls:
                        for prod_tmpl in prod_tmpls:
                            li.append(prod_tmpl.id)
                        print("LI",li)
                        domain['product_id'] = [('id', 'in', li)]
                        return {'domain': domain}
            else:
                if line.product_category_id:
                    line.product_id = False
                    prod_tmpls = line.env['product.product'].search(
                        [('categ_id', '=', line.product_category_id.id)])
                    if prod_tmpls:
                        for prod_tmpl in prod_tmpls:
                            li.append(prod_tmpl.id)
                        domain['product_id'] = [('id', 'in', li)]
                        return {'domain': domain}
                # else:
                #     domain['product_tmpl_id'] = [('id', 'in', [])]
                #     domain['product_id'] = [('id','in',[])]
                #     return {'domain':domain}
 
   #Created by Ajinkya on  25/06/2019
    # @api.onchange('product_tmpl_id')
    # def onchng_set_prod_prod(self):
    #     li=[]
    #     domain={}
    #     if self.product_tmpl_id:
    #         if self.product_tmpl_id.product_variant_ids:
    #             for i in self.product_tmpl_id.product_variant_ids:
    #                 li.append(i.id)
    #             domain['product_id']=[('id','in',li)]
    #             return {'domain':domain}
    #         else:
    #             domain['product_id'] = [('id','in',[])]
    #             return {'domain':domain}
    
    @api.onchange('product_label','logic_selection')
    def onchnge_set_product_var(self):
        # prod_obj=self.env[].browse(self.product_label)
        if self.logic_selection == "and":
            if self.product_label:
                li=[]
                domain={}
                for i in self.product_label:
                    for j in i.prod_ids:
                        #print("===>j",j)
                        prods=self.env['product.product'].search([('product_tmpl_id','=',j.id)])
                        for z in prods:
                            if z.categ_id==self.product_category_id:
                                li.append(z.id)
                    #print("li=======+>",li)
                    domain['product_id']=[('id','in',li)]
                    li=[]
                return {'domain':domain}
            else:
                for line in self:
                    li = []
                    domain = {}
                    if 'default_product_category_id' in self.env.context:
                        if self.env.context['default_product_category_id']:
                            line.product_id = False 
                            #print("Default Category id ",self.env.context['default_product_category_id'])
                            prod_tmpls = line.env['product.product'].search(
                                [('categ_id', '=', self.env.context['default_product_category_id'])])
                            #print("Prod Temps",prod_tmpls)
                            if prod_tmpls:
                                for prod_tmpl in prod_tmpls:
                                    li.append(prod_tmpl.id)
                                print("LI",li)
                                domain['product_id'] = [('id', 'in', li)]
                                return {'domain': domain}
                    else:
                        if line.product_category_id:
                            line.product_id = False
                            prod_tmpls = line.env['product.product'].search(
                                [('categ_id', '=', line.product_category_id.id)])
                            if prod_tmpls:
                                for prod_tmpl in prod_tmpls:
                                    li.append(prod_tmpl.id)
                                domain['product_id'] = [('id', 'in', li)]
                                return {'domain': domain}
            #     domain={}
            #     li=[]
            #     self.product_id=False
            #     domain['product_id']=[('id','in',li)]
            #     return {'domain':domain}
        else:
            if self.product_label:
                li=[]
                domain={}
                for i in self.product_label:
                    for j in i.prod_ids:
                        #print("===>j",j)
                        prods=self.env['product.product'].search([('product_tmpl_id','=',j.id)])
                        for z in prods:
                            if z.categ_id==self.product_category_id:
                                li.append(z.id)
                    #print("li=======+>",li)
                domain['product_id']=[('id','in',li)]
                return {'domain':domain}
            else:
                for line in self:
                    li = []
                    domain = {}
                    if 'default_product_category_id' in self.env.context:
                        if self.env.context['default_product_category_id']:
                            line.product_id = False 
                            #print("Default Category id ",self.env.context['default_product_category_id'])
                            prod_tmpls = line.env['product.product'].search(
                                [('categ_id', '=', self.env.context['default_product_category_id'])])
                            #print("Prod Temps",prod_tmpls)
                            if prod_tmpls:
                                for prod_tmpl in prod_tmpls:
                                    li.append(prod_tmpl.id)
                                print("LI",li)
                                domain['product_id'] = [('id', 'in', li)]
                                return {'domain': domain}
                    else:
                        if line.product_category_id:
                            line.product_id = False
                            prod_tmpls = line.env['product.product'].search(
                                [('categ_id', '=', line.product_category_id.id)])
                            if prod_tmpls:
                                for prod_tmpl in prod_tmpls:
                                    li.append(prod_tmpl.id)
                                domain['product_id'] = [('id', 'in', li)]
                                return {'domain': domain}
            #     domain={}
            #     li=[]
            #     self.product_id=False
            #     domain['product_id']=[('id','in',li)]
            #     return {'domain':domain}
    

class quotation_bom_line(models.Model):
    _name = "quotation.bom.line"
    _parent_name = "bom_parent_id"
    _parent_store = True
    _parent_order = 'name'
    _rec_name = 'qbom_id'
    _order = 'parent_left'

    def name_get(self):
        result = []
        for rec in self:
            if rec.product_id.name:
                name = rec.product_id.name_get()[0][1]
            else:
                name = ""
            if rec.qbom_id:
                bom_name = rec.qbom_id.name
            else:
                bom_name = ""
            if rec.name:
                rec_name = rec.name
            else:
                rec_name = ""
            result.append((rec.id, bom_name + ' ' + name+'--'+rec_name))

        return result
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)
    
    product_label = fields.Many2many(
        'product.label', 'product_label_quotation_bom_line_rel', 'qbomline_id', 'label_id', string="Labels")
    bom_parent_id = fields.Many2one(
        'quotation.bom.line', string="Quote Parent Item", index=True, help="Quote Item Parent",ondelete='cascade')#,domain=lambda self:self.set_bom_parent_id())
    child_id = fields.One2many(
        'quotation.bom.line', 'bom_parent_id', string="Immidiate Child Items")
    super_parent_id = fields.Many2one(
        'quotation.bom.line', string="Super Parent Item")
    super_bom_child_ids = fields.One2many(
        'quotation.bom.line', 'super_parent_id', string="All Child Items")
    immi_parent_id = fields.Many2one('product.product',string="Parent Item")
    immi_parent_child_ids=fields.One2many('quotation.bom.line','immi_parent_id')
    qbom_id = fields.Many2one("quotation.bom",ondelete='cascade',index=False,required=False)
    name = fields.Char("Description", required=True,
                       help="Description of the Product")
    product_tmpl_id = fields.Many2one(
        'product.template', string="Product Template", default=lambda self: self.product_id.product_tmpl_id, help="The Product Template for which you will be selecting the Appropriate Variant")
    level = fields.Char(string="Level")
    product_id = fields.Many2one(
        'product.product', string="Product", help="Actual Product / Item ")
    product_qty = fields.Float(
        'Product Quantity', help="Quantity of the product", default=1.00)
    product_orig_qty=fields.Float('Product Quantity', help="Quantity  as in Er. BOM", default=1.00)
    product_uom_id = fields.Many2one('product.uom', 'Unit of Measure', oldname='product_uom',default=lambda self: self.env['product.uom'].search([('name','=','Unit(s)')]),
                                     help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control")
    # sequence = fields.Integer('Sequence', default=1,help="Gives the sequence order when displaying.")
    weight = fields.Float(string="Wt. (kg)", help="weight im kg",compute="_set_child_weight",store=True,readonly=False)
    computed_weight = fields.Float(
        string="Reference Weight", compute="set_weight",store=True)
    active = fields.Boolean('Active', default=True)
    purchase_price = fields.Float(string="Cost Price",compute="_set_purchase_cost",readonly=False,store=True)
    computed_cost = fields.Float(
        string="Computed Cost", compute='set_price_unit', store=True, readonly=True)
    price_subtotal = fields.Float(
        string='Sub Total', readonly=True, compute='set_price_subtotal', store=True, default=0.00)
    new_price_unit = fields.Float(string="Sale Price", default=0.00)
    manufacture_oh = fields.Float(string="MOH (%)", help="MOH % of Unit Price")
    bo_oh = fields.Float(string="BOH (%)", help="BOH % of Unit Price")
    manu_oh_amt = fields.Float(string="MOH (₹)",
                               readonly=True, store=True, compute='set_mo_oh_amt', default=0.00, help="amount calculated in cosideration of Unit Price")
    boh_amt = fields.Float(string="BOH (₹)", readonly=True,
                           store=True, compute="set_bo_oh_amt", default=0.00, help="Amount calculated with cosideration of Unit Price")

    margin = fields.Float(string="Margin (₹)")
    
    product_category_id = fields.Many2one("product.category", string="Product Category",default=lambda self:self.product_id.categ_id)
    transaction_lines = fields.One2many("transaction.info", "qbom_line_id")
    transaction_count = fields.Integer(compute="get_transactions_count")
    weight_rate = fields.Float(
        string="Wt./Per kg", help="The rate of the weight specified per kg",default=0.0)
    
    qbom_tmpl_id=fields.Many2one('quotation.bom.line',string="Quotation BOM")
    bom_tmpl_id=fields.Many2one('mrp.bom',string="Engineering BOM")
    functional_categ_id=fields.Many2one('product.category',string="Functional Category")
    indent_design=fields.Text(string="Indent Level",compute='set_indent_level',store=True)
    copy_from = fields.Selection(string='Copy From', selection=[(
        'qbom', 'Quotation BOM'), ('bom', 'Engineering BOM')])
    product_default_code = fields.Char("Product Default Code" ,compute = '_onchange_set_defaultcode',store=True,readonly=False)
    product_doc_file = fields.Binary(string="Word Doc", attachment="True")
    filename = fields.Char("Filename")
    logic_selection=fields.Selection([('and','AND'),('or','OR')],string="Labels AND / OR")
    @api.depends('level')
    def set_indent_level(self):
        for order in self:
            sp="    "
            sy="="
            order.indent_design=sp*int(order.level)+sy*int(order.level)
    # @api.depends('transaction_lines.total_weight')
    # def set_computed_weight(self):
    #     for order in self:
    #         if order.transaction_lines:
    #             for j in order.transaction_lines:
    #                 order.computed_weight = j.total_weight
    @api.onchange('bom_parent_id','level')
    def set_bom_parent_id(self):
        # print("########################################",self.env.context)
        domain={}
        li=[]
        li1=[]
        if 'default_qbom_id' in self.env.context:
            qbom_id=self.env.context['default_qbom_id']
            qbom_obj=self.env['quotation.bom'].browse(qbom_id)
            level= self.level
        # for order in self:
            # if order.qbom_lines:
            #     for i in order.qbom_lines:
            for i in qbom_obj:
                if i.qbom_lines:
                    for j in i.qbom_lines:
                        if self.level:
                            if j.level == str(int(level)-1):
                                li1.append(j.id)
                        else:
                            li.append(j.id)
            if li:
                li.pop()
                domain['bom_parent_id']=[('id', 'in', li)]
            else:
                domain['bom_parent_id']=[('id', 'in', li1)]
            return {'domain':domain}
    @api.multi
    def compute_cost(self):
        for qbom_line in self:
            if qbom_line.product_category_id:
                form = self.env['ir.model.data'].xmlid_to_res_id(
                    'quotation_bom.transaction_formula_form_view', raise_if_not_found=True)

                result = {'name': 'transaction_info_form',
                          'view_type': 'form',
                          'res_model': 'transaction.info',
                          'view_id': form,
                          'context': {
                              'default_product_category_id': qbom_line.product_category_id.id,
                              'default_qbom_line_id': qbom_line.id
                          },
                          'type': 'ir.actions.act_window',
                          'view_mode': 'form'
                          }
                return result
            else:
                raise UserError(_('Please Specify Product Category'))

    # @api.onchange('computed_cost')
    # def _onchange_computedcost(self):
    #     for order in self:
    #         if order.computed_cost:
    #             order.purchase_price = order.computed_cost
    #             return {'value':{'purchase_price':order.computed_cost}}
    @api.depends('transaction_lines.qbom_line_id')
    def get_transactions_count(self):
        for i in self:
            if i.transaction_lines:
                nbr = 0
                for line in i.transaction_lines:
                    nbr += 1
                i.transaction_count = nbr

    @api.depends('purchase_price', 'computed_cost', 'manufacture_oh')
    def set_mo_oh_amt(self):
        for qbomline in self:
            # if qbomline.computed_cost:
            #     qbomline.manu_oh_amt = (
            #         qbomline.computed_cost * qbomline.manufacture_oh)/100
            # else:
            qbomline.manu_oh_amt = (
                qbomline.purchase_price * qbomline.manufacture_oh)/100

    @api.depends('purchase_price', 'computed_cost', 'bo_oh')
    def set_bo_oh_amt(self):
        for qbomline in self:
            # if qbomline.computed_cost:
            #     qbomline.boh_amt = (qbomline.computed_cost*qbomline.bo_oh)/100
            # else:
            qbomline.boh_amt = (qbomline.purchase_price*qbomline.bo_oh)/100

    @api.depends('margin')
    def set_margin_amt(self):
        for qbomline in self:
            # if qbomline.computed_cost:
            #     qbomline.margin_amt = (
            #         qbomline.computed_cost * qbomline.margin)/100
            # else:
            qbomline.margin_amt = (
                qbomline.purchase_price*qbomline.margin)/100

   
    
    #Created by Ajinkya and Jeevan on  24/06/2019
    @api.depends('purchase_price', 'product_qty', 'bo_oh', 'manufacture_oh', 'margin', 'weight','weight_rate')
    def set_price_subtotal(self):
        # for order in self:
        #     if order.weight == 0 and order.weight_rate==0.0:
        #         order.update({
        #             'price_subtotal': (order.product_qty * order.purchase_price) + order.manu_oh_amt + order.boh_amt + order.margin
        #         })
        #     else:
        #         order.update({
        #             'price_subtotal': (order.weight_rate * order.weight) + order.manu_oh_amt + order.boh_amt + order.margin
        #         })
        li=[]
        for order in self:
            weight_cost=order.weight*order.weight_rate
            li.append(order.purchase_price)
            li.append(order.new_price_unit)
            li.append(weight_cost)
            max_cost=max(li)
            li=[]
            order.update({
                'price_subtotal':(max_cost * order.product_qty) + order.manu_oh_amt + order.boh_amt + order.margin
            })
    #Set Computed Price
    #Created by Ajinkya and Jeevan on  25/06/2019
    @api.depends('child_id.price_subtotal')
    def set_price_unit(self):
        for order in self:
            computed_cost=0.0
            for child in order.child_id:
                computed_cost += child.price_subtotal
            order.computed_cost = computed_cost
    #Set Purchase Price
    #Created by Ajinkya and Jeevan on  25/06/2019                                                                                     
    @api.depends('computed_cost')
    def _set_purchase_cost(self):
        for order in self:
            if order.child_id:
                order.purchase_price=order.computed_cost
            else:
                order.purchase_price=order.product_id.standard_price
    
    #Created by Ajinkya and Jeevan on  25/06/2019
    @api.depends('child_id.weight')
    def set_weight(self):
        for order in self:
            computed_cost=0.0
            for child in order.child_id:
                computed_cost += child.weight
            order.computed_weight = computed_cost
    #Set Purchase Price

    #Created by Ajinkya and Jeevan on  25/06/2019
    @api.depends('computed_weight')
    def _set_child_weight(self):
        for order in self:
            if order.child_id:
                order.weight=order.computed_weight
            else:
                order.weight=order.product_id.weight

    @api.onchange('product_category_id')
    def onchng_set_prod_template(self):
        for line in self:
            li = []
            domain = {}
            if line.product_category_id:
                line.product_id = False
                prod_tmpls = line.env['product.product'].search(
                    [('categ_id', '=', line.product_category_id.id)])
                if prod_tmpls:
                    for prod_tmpl in prod_tmpls:
                        li.append(prod_tmpl.id)
                    domain['product_id'] = [('id', 'in', li)]
                    return {'domain': domain}
                else:
                    domain['product_id'] = [('id','in',[])]
                    return {'domain':domain}

    
    @api.model
    def _get_qbom_child_vals(self, record, level, qty, uom):
        child = {
            "name": record.product_id.name or record.product_id.product_tmpl_id.name or record.product_id.product_tmpl_id.categ_id.name,
            "product_id": record.product_id,
            "product_tmpl_id": record.product_id.product_tmpl_id,
            "product_qty": record.product_qty,
            "product_uom_id": record.product_uom_id,
            "product_category_id": record.product_id.product_tmpl_id.categ_id,
            "purchase_price": record.product_id.standard_price,
            "new_price_unit": record.product_id.lst_price,
            "level": level,
            'immi_parent_id': record.bom_parent_id.product_id,
            'product_orig_qty':record.product_qty
        }
        qty_per_bom = record.bom_parent_id.product_qty
        if uom:
            if uom != record.bom_parent_id.product_uom_id:
                qty = uom._compute_quantity(qty, record.bom_parent_id.product_uom_id)
            child['product_qty'] = (record.product_qty * qty) / qty_per_bom
        else:
            # for the first case, the ponderation is right
            child['product_qty'] = (record.product_qty * qty)
        return child

    def get_qbom_children(self, records, level=0,qty=1.0):
        result = []

        def _get_qbom_rec(records, level, qty=1.0, uom=False):
            for l in records:
                child = self._get_qbom_child_vals(l, level, qty, uom)
                result.append((0, 0, child))
                if l.child_id:
                    level += 1
                    _get_qbom_rec(l.child_id, level,
                             qty=child['product_qty'], uom=child['product_uom_id'])
                    if level > 0:
                        level -= 1
            return result

        children = _get_qbom_rec(records, level,qty=qty)

        return children
    @api.model
    def create(self, vals):
        vals['active']=True
        new_id=super(quotation_bom_line, self).create(vals)
        for order in new_id:
            if order.level != '0':
                if not(order.bom_parent_id):
                    qbom_line_obj=order.env['quotation.bom.line']
                    par_ids = qbom_line_obj.search(
                        [('qbom_id', '=', order.qbom_id.id), ('product_id', '=', order.immi_parent_id.id)])
                    if par_ids:
                        j=max(par_ids.ids)
                        order.bom_parent_id = qbom_line_obj.browse(j)
                        order.qbom_id=qbom_line_obj.browse(j).qbom_id
                else:
                    order.immi_parent_id = order.bom_parent_id.product_id
                    order.qbom_id=order.bom_parent_id.qbom_id
            if order.bom_tmpl_id and not(order.child_id):
                li1=order.qbom_id.get_children(order.bom_tmpl_id.bom_line_ids,level=int(order.level)+1,qty=order.product_qty)
                for i in li1:
                    values={
                        "name": i[2]['name'],
                        "product_id": i[2]['product_id'].id,
                        "product_tmpl_id": i[2]['product_tmpl_id'].id,
                        "product_qty": i[2]['product_qty'],
                        "product_uom_id": i[2]['product_uom_id'].id,
                        "product_category_id": i[2]['product_category_id'].id,
                        "purchase_price": i[2]['purchase_price'],
                        "new_price_unit": i[2]['new_price_unit'],
                        "level": i[2]['level'],
                        'immi_parent_id': i[2]['immi_parent_id'].id,
                        'product_orig_qty':i[2]['product_orig_qty'],
                        'qbom_id':order.qbom_id.id
                    }
                    self.create(values)
            if order.qbom_tmpl_id and not(order.child_id):
                li2=order.get_qbom_children(order.qbom_tmpl_id.child_id,level=int(order.level)+1,qty=order.product_qty)
                print("@@@@@@@@###############=============>",li2)
                for z in li2:
                    values={
                            "name": z[2]['name'],
                            "product_id": z[2]['product_id'].id,
                            "product_tmpl_id": z[2]['product_tmpl_id'].id,
                            "product_qty": z[2]['product_qty'],
                            "product_uom_id": z[2]['product_uom_id'].id,
                            "product_category_id": z[2]['product_category_id'].id,
                            "purchase_price": z[2]['purchase_price'],
                            "new_price_unit": z[2]['new_price_unit'],
                            "level": z[2]['level'],
                            'immi_parent_id': z[2]['immi_parent_id'].id,
                            'qbom_id':order.qbom_id.id
                    }
                    self.create(values)    
        return new_id

    #method to set mrp bom related to the product in the dropdown
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
                return {'domain':domain}
            else:
                domain['bom_tmpl_id'] = [('id', 'in', [])]
                return {'domain':domain}
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
                return {'domain':domain}
            else:
                domain['bom_tmpl_id'] = [('id', 'in', [])]
                return {'domain':domain}
    #method to set quotation bom related to the product in the dropdown                
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
                ['&',('product_tmpl_id', '=', prod_tmpl_obj.id), ('product_id', '=', prod_prod_obj.id)])
            if qbom_objs:
                for prod in qbom_objs:
                    li.append(prod.id)
                domain['qbom_tmpl_id'] = [('id', 'in', li)]
                return {'domain':domain}
            else:
                domain['qbom_tmpl_id'] = [('id', 'in', [])]
                return {'domain':domain}
        else:
            li = []
            domain = {}
            prod_tmpl_obj = self.env['product.template'].browse(
                self.product_tmpl_id.id)
            qbom_objs=self.env['quotation.bom.line'].search([('product_tmpl_id', '=', prod_tmpl_obj.id)])
            if qbom_objs:
                for prod in qbom_objs:
                    li.append(prod.id)
                domain['qbom_template_id'] = [('id', 'in', li)]
                return {'domain':domain}
            else:
                domain['qbom_template_id'] = [('id', 'in', [])]
                return {'domain':domain}
    @api.onchange('product_id')
    def onchng_set_bom(self):
        '''
            Method to set Engineering Bom in drop down 
            based on the Product Template and Product ID
        '''
        if self.product_id and self.product_tmpl_id:
            self.weight = self.product_id.weight
            self.product_uom_id = self.product_id.uom_id
        elif self.product_tmpl_id:
            self.weight = self.product_tmpl_id.weight
            self.product_uom_id = self.product_id.uom_id
            self.product_doc_file = self.product_id.product_doc

    @api.onchange('product_id', 'product_uom_id')
    def onchng_set_price_unit(self):
        if self.product_id:
            self.new_price_unit = self.product_id.uom_id._compute_price(
                self.product_id.lst_price, self.product_uom_id)
            # self.product_default_code = self.product_id.default_code  
            self.product_doc_file = self.product_id.product_doc 
        # if not self.child_id:
        #     self.purchase_price = self.product_id.uom_id._compute_price(
        #         self.product_id.standard_price, self.product_uom_id)

    def set_qty(self,recs,qty=1.0):

        def set_rec_qty(recs,qty=1.0):
            for i in recs:
                i.product_qty=qty*i.product_orig_qty
                if i.child_id:
                    set_rec_qty(i.child_id,i.product_qty)
        set_rec_qty(recs,qty=qty)
    # @api.onchange('product_tmpl_id')
    # def onchng_set_prod_prod(self):
    #     li=[]
    #     domain={}
    #     if self.product_tmpl_id:
    #         if self.product_tmpl_id.product_variant_ids:
    #             for i in self.product_tmpl_id.product_variant_ids:
    #                 li.append(i.id)
    #             domain['product_id']=[('id','in',li)]
    #             return {'domain':domain}
    #         else:
    #             domain['product_id'] = [('id','in',[])]
    #             return {'domain':domain}

    @api.depends('product_id')
    def _onchange_set_defaultcode(self):
        for order in self:
            if order.product_id:
                order.product_default_code = order.product_id.default_code
                print("#########",order.product_default_code)
    @api.multi 
    def write(self,vals):

        if vals:
            if 'product_qty' in vals:
                self.set_qty(self.child_id,qty=vals['product_qty'])
        new_id = super(quotation_bom_line, self).write(vals)
        return new_id


     #Created by Jeevan on 24/06/2019
    @api.multi
    def action_child_items(self):
        tree = self.env['ir.model.data'].xmlid_to_res_id(
                    'quotation_bom.quotation_bom_line_new_tree_children', raise_if_not_found=True) 
        for order in self:
            if order.child_id:
                domain=[('id','child_of',order.id)]
                # print("domain",domain)
                result= {
                            'name': 'Child Items',
                            'res_model': 'quotation.bom.line',
                            'view_id': tree,
                            'domain':domain,
                            'context': {
                                'default_qbom_id': order.qbom_id.id,
                                'search_default_qbom_id': order.qbom_id.id
                            },
                            'type': 'ir.actions.act_window',
                            'view_mode': 'tree'
                        }
                # print("result",result)
                return result
            else:
                raise UserError(_("There are no child for this product"))



    @api.onchange('product_label','logic_selection')
    def onchnge_set_product_var(self):
        # prod_obj=self.env[].browse(self.product_label)
        if self.logic_selection == "and":
            if self.product_label:
                li=[]
                domain={}
                for i in self.product_label:
                    for j in i.prod_ids:
                        #print("===>j",j)
                        prods=self.env['product.product'].search([('product_tmpl_id','=',j.id)])
                        for z in prods:
                            if z.categ_id==self.product_category_id:
                                li.append(z.id)
                    #print("li=======+>",li)
                    domain['product_id']=[('id','in',li)]
                    li=[]
                return {'domain':domain}
            else:
                for line in self:
                    li = []
                    domain = {}
                    if 'default_product_category_id' in self.env.context:
                        if self.env.context['default_product_category_id']:
                            line.product_id = False 
                            #print("Default Category id ",self.env.context['default_product_category_id'])
                            prod_tmpls = line.env['product.product'].search(
                                [('categ_id', '=', self.env.context['default_product_category_id'])])
                            #print("Prod Temps",prod_tmpls)
                            if prod_tmpls:
                                for prod_tmpl in prod_tmpls:
                                    li.append(prod_tmpl.id)
                                print("LI",li)
                                domain['product_id'] = [('id', 'in', li)]
                                return {'domain': domain}
                    else:
                        if line.product_category_id:
                            line.product_id = False
                            prod_tmpls = line.env['product.product'].search(
                                [('categ_id', '=', line.product_category_id.id)])
                            if prod_tmpls:
                                for prod_tmpl in prod_tmpls:
                                    li.append(prod_tmpl.id)
                                domain['product_id'] = [('id', 'in', li)]
                                return {'domain': domain}
            #     domain={}
            #     li=[]
            #     self.product_id=False
            #     domain['product_id']=[('id','in',li)]
            #     return {'domain':domain}
        else:
            if self.product_label:
                li=[]
                domain={}
                for i in self.product_label:
                    for j in i.prod_ids:
                        #print("===>j",j)
                        prods=self.env['product.product'].search([('product_tmpl_id','=',j.id)])
                        for z in prods:
                            if z.categ_id==self.product_category_id:
                                li.append(z.id)
                    #print("li=======+>",li)
                domain['product_id']=[('id','in',li)]
                return {'domain':domain}
            else:
                for line in self:
                    li = []
                    domain = {}
                    if 'default_product_category_id' in self.env.context:
                        if self.env.context['default_product_category_id']:
                            line.product_id = False 
                            #print("Default Category id ",self.env.context['default_product_category_id'])
                            prod_tmpls = line.env['product.product'].search(
                                [('categ_id', '=', self.env.context['default_product_category_id'])])
                            #print("Prod Temps",prod_tmpls)
                            if prod_tmpls:
                                for prod_tmpl in prod_tmpls:
                                    li.append(prod_tmpl.id)
                                print("LI",li)
                                domain['product_id'] = [('id', 'in', li)]
                                return {'domain': domain}
                    else:
                        if line.product_category_id:
                            line.product_id = False
                            prod_tmpls = line.env['product.product'].search(
                                [('categ_id', '=', line.product_category_id.id)])
                            if prod_tmpls:
                                for prod_tmpl in prod_tmpls:
                                    li.append(prod_tmpl.id)
                                domain['product_id'] = [('id', 'in', li)]
                                return {'domain': domain}

            #     domain={}
            #     li=[]
            #     self.product_id=False
            #     domain['product_id']=[('id','in',li)]
            #     return {'domain':domain}

# string='Customer'
# res_pat= search.env['res.patner'].search([])
# for i in res_pat:
#     if  i.customer == True:
#         print("customer name",i.name)
#         i.name=chr(ord(string)+1)
#         print("Name Change",i.name)

