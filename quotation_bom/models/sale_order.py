from odoo import api, fields, models, _

# from odoo.resume_parser.resume_parser.resume_parser import ResumeParser
import os
# import docx2txt
# import docx
import base64
import codecs
import io
# import datetime
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError
#from datetime import datetime, timedelta
#Created By Ajinkya Joshi on 11/10/2019
from PyPDF2 import PdfFileMerger
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen.canvas import Canvas
from pdfrw import PdfReader
from pdfrw.toreportlab import makerl
from pdfrw.buildxobj import pagexobj
# import PDFWriter
from PyPDF2 import PdfFileMerger
import datetime
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph
from reportlab.rl_config import defaultPageSize
import subprocess
from pdfrw import PdfReader




class SaleOrder(models.Model):

    _inherit = "sale.order"

    def set_current_date(self):
        for order in self:
            order.cur_time = datetime.datetime.today()

    cur_time = fields.Date(
        string='Today', compute='set_current_date')
    total_weight = fields.Float(
        "Total Weight",
        compute="_compute_weight_total",
        store=True,
        track_visibility="onchange",
    )
    dealer_margin = fields.Float(
        "Dealer Margin (%)", default=0.0, track_visibility="onchange"
    )
    converted_doc_file = fields.Binary(
        string=u"Converted File", attachment="True")
    filename = fields.Char("Filename")
    total_discount_detail = fields.Float(
        "Total Discount (%)", compute="_check_discount", store=True
    )
    order_line_approve = fields.One2many("approval.info", "order_approve_id")
    approve_flag = fields.Boolean(default=False)
    general_budget_ids=fields.Many2many('account.budget.post','sale_order_budget_pos_rel','order_id','gen_budget_id')
    new_state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("tobeapproved", "To Be Approved"),
            ("approved", "Approved"),
            ("sent", "Quotation Sent"),
            ("presale", "Sales Order"),
            ("sale", "Released"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="State",
        readonly=True,
        store=True,
        copy=False,
        index=True,
        track_visibility="onchange",
        default="draft",
    )

    # To Unapprove the quotation
    @api.multi
    def action_unapprove(self):
        for order in self:
            if order.total_discount_detail > 0:
                order.new_state = "tobeapproved"
            elif order.total_discount_detail < 0:
                order.new_state = "approved"

    def change_approve_flag(self):
        approve_list1 = []
        approve_list2 = []
        for order in self:
            if order.order_line_approve:
                for line in order.order_line_approve:
                    if line.approve_status == False:
                        approve_list1.append(line.approve_status)
                        print("approve_list1=======>", approve_list1)
                    else:
                        approve_list2.append(line.approve_status)
                        print("approve_list2==========>", approve_list2)
            if len(approve_list1) == 0:
                order.approve_flag = True
            else:
                order.approve_flag = False

    @api.multi
    def action_validate(self):
        for order in self:
            if order.order_line_approve:
                for ids in order.order_line_approve:
                    if ids.users.id == self.env.uid:
                        ids.approve_status = True
            else:
                order.approve_flag = True
        self.change_approve_flag()

    @api.multi
    def action_cancel(self):
        for order in self:
            if order.order_line_approve:
                for line in order.order_line_approve:
                    if line.approve_status == True:
                        line.approve_status = False
                order.approve_flag = False
        return self.write({"state": "cancel", "new_state": "cancel"})

    @api.multi
    def action_confirm(self):
        # for order in self:
        #     if order.order_line_approve:
        #         for line in order.order_line_approve:
        #             if line.approve_status == True:
                        # for order in self.filtered(
                        #     lambda order: order.partner_id
                        #     not in order.message_partner_ids
                        # ):
                        #     order.message_subscribe([order.partner_id.id])
                        # self.write(
                        #     {
                        #         "state": "sale",
                        #         "new_state": "sale",
                        #         "confirmation_date": fields.Datetime.now(),
                        #     }
                        # )
                        # if self.env.context.get("send_email"):
                        #     self.force_quotation_send()

                        # create an analytic account if at least an expense product
                        # for order in self:
                        #     if any(
                        #         [
                        #             expense_policy != "no"
                        #             for expense_policy in order.order_line.mapped(
                        #                 "product_id.expense_policy"
                        #             )
                        #         ]
                        #     ):
                        #         if not order.analytic_account_id:
                        #             order._create_analytic_account()

                        return super(SaleOrder,self).action_confirm()
                    # else:
                    #     raise UserError(
                    #         _("Cannot Release.Approvals are pending"))
    
    def set_qbom_state(self):
        '''
            This method changes the state of quotation bom to "sale".
        '''
        for order in self:
            # Changed by ajinkya joshi on 07/10/2019 
            # Before updating if order.new_state =="sale"
           if order.new_state =="presale":
               if order.order_line:
                   for line in order.order_line:
                       if line.qbom_ids:
                           for qbom in line.qbom_ids:
                               if qbom.state == 'quotation':
                                   qbom.state = "sale"
    def create_project_tmpl(self):
        '''
            When Quotation -> Sales Order
            then this method creates a Project with Sales Order number 
            and some tasks mentioned in the method.
        '''
        for order in self:
            if order.new_state=="presale":        
                vals={}
                vals['name']=order.name
                vals['partner_id']=order.partner_id.id
                project_id=order.env['project.project'].create(vals)
                print("Analytic Account=====>",project_id.analytic_account_id)
                order.analytic_account_id=project_id.analytic_account_id
                order.env['project.task'].create({'name':order.name+' '+'Design','project_id':project_id.id})
                order.env['project.task'].create({'name':order.name+' '+'Manufacturing','project_id':project_id.id})
                order.env['project.task'].create({'name':order.name+' '+'Logistics','project_id':project_id.id})
                order.env['project.task'].create({'name':order.name+' '+'Installation And Commission','project_id':project_id.id})    
                order.env['project.task'].create({'name':order.name+' '+'Procurement','project_id':project_id.id})

    #Created by Ajinkya Joshi on 11/10/2019
    def combine_pdf(self,files):
        from reportlab.lib.units import inch
        print("Hello")
        merger = PdfFileMerger()
        for pdf in files:
            merger.append(pdf)
        merger.write("/home/jeevan/odoo-11.0/Doc_files/"+"Solution file"+str(datetime.datetime.today().date())+self.name+".pdf")
        merger.close()

        input_file = "/home/jeevan/odoo-11.0/Doc_files/"+"Solution file"+str(datetime.datetime.today().date())+self.name+".pdf"
        output_file = "/home/jeevan/odoo-11.0/Doc_files/"+"Solution file"+str(datetime.datetime.today().date())+self.name+".pdf"

        reader = PdfReader(input_file)
        pages = [pagexobj(p) for p in reader.pages]

        canvas = Canvas(output_file)

        PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]
        
        
        Title = "Veeraja Industries Pvt Ltd."
        Title1 = "Date:"+self.date_order+"          "+"Proposal No:"+self.name+"               "+"Revision:"+' '
        for page_num, page in enumerate(pages, start=1):

            # Add page
            canvas.setPageSize((page.BBox[2], page.BBox[3]))
            canvas.doForm(makerl(canvas, page))

            # Draw footer
            footer_text = "Page %s of %s" % (page_num, len(pages))
            x = 128
            canvas.saveState()
            canvas.setFillColorRGB(1,0,0)
            canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-50, Title)
            canvas.setFillColorRGB(1,0,0)
            canvas.drawCentredString(PAGE_WIDTH/2.1, PAGE_HEIGHT-70,Title1)
            # canvas.setFillColorRGB(255,255,0)
            # canvas.rect(1*inch,10.6*inch,6*inch,0.3*inch, fill=1)
            canvas.setFont('Times-Roman',9)
            canvas.setStrokeColorRGB(0, 0, 0)
            canvas.setFont('Times-Roman', 10)
            canvas.drawCentredString(page.BBox[2]-x, 80, footer_text)
            canvas.restoreState()

            canvas.showPage()

        canvas.save()

        for top, dirs, files in os.walk('/home/jeevan/odoo-11.0/Doc_files/'):
            for filename in files:
                if filename.endswith('.pdf'):
                    abspath = os.path.join(top, filename)
                    subprocess.call('lowriter --invisible --convert-to docx "{}"'
                                    .format(abspath), shell=True)
                    print("Convert Done")


        with open(output_file, "rb") as f:
            document = f.read()
            self.converted_doc_file = base64.b64encode(document)
            self.filename = "Final Solution file" +str(datetime.datetime.today().date()) +"_"+self.name+".pdf"
            
            os.remove(
            "/home/jeevan/odoo-11.0/Doc_files/"
            + "Solution file"
            + str(datetime.datetime.today().date())
            +self.name
            + ".pdf"
        )


    #Created By Ajinkya Joshi on 11/10/2019
    @api.multi
    def merge_file(self):
        li=[]
        # count, number_of_files = 0
        # filename_master="/home/jeevan/odoo-11.0/Doc_files/file1.docx"
        for order in self:
            if order.order_line:
                for i in order.order_line:
                    if i.qbom_ids:
                        for j in i.qbom_ids:
                            for z in j.qbom_lines:
                                if z.level == '0':
                                    if z.upload_pdf_file: 
                                        li.append(io.BytesIO(base64.b64decode(codecs.decode(z.upload_pdf_file))))
                                    print(li)
                                    # else:
                                    #     raise UserError(_("Please Upload the Product Document for the Product %s")%z.product_id.product_tmpl_id.name)
        self.combine_pdf(li)

    # def _get_general_budget_id_manufaturing(self):
    #     gen_budget_id=self.env['account.budget.post'].search([('name','=','Manufacture Head')])
    #     if gen_budget_id:
    #         return gen_budget_id
    #     else:
    #         raise UserError(_("Budgetory Position for manufacturing is missing please Create same"))
    # def _get_general_budget_id_manufaturing(self):
    #     gen_budget_id=self.env['account.budget.post'].search([('name','=','Manufacture Head')])
    #     if gen_budget_id:
    #         return gen_budget_id
    #     else:
    #         raise UserError(_("Budgetory Position for manufacturing is missing please Create same"))
    # def _get_general_budget_id_design(self):
    #     gen_budget_id=self.env['account.budget.post'].search([('name','=','Design Head')])
    #     if gen_budget_id:
    #         return gen_budget_id
    #     else:
    #         raise UserError(_("Budgetory Position for manufacturing is missing please Create same"))
    # def _get_general_budget_id_logistics(self):
    #     gen_budget_id=self.env['account.budget.post'].search([('name','=','Logistics Head')])
    #     if gen_budget_id:
    #         return gen_budget_id
    #     else:
    #         raise UserError(_("Budgetory Position for manufacturing is missing please Create same"))
    # def _get_general_budget_id_procurement(self):
    #     gen_budget_id=self.env['account.budget.post'].search([('name','=','Procurement Head')])
    #     if gen_budget_id:
    #         return gen_budget_id
    #     else:
    #         raise UserError(_("Budgetory Position for manufacturing is missing please Create same"))
    def create_budget_tmpl(self):
        for  order in self:
            if order.new_state=="presale":        
                vals={}
                vals['name']=order.name
                vals["budget_amount"]=self.calculate_total()
                budget_id=order.env['crossovered.budget'].create(vals)
                # manu_gen_budget_id=order._get_general_budget_id_manufaturing()
                # manu_gen_budget_id=order._get_general_budget_id_design()
                # manu_gen_budget_id=order._get_general_budget_id_logistics()
                # manu_gen_budget_id=order._get_general_budget_id_installation()
                # manu_gen_budget_id=order._get_general_budget_id_procurement()
                for i in order.general_budget_ids:
                    vals={'crossovered_budget_id':budget_id.id,'analytic_account_id':order.analytic_account_id.id,'general_budget_id':i.id,'planned_amount':100.0}
                    order.env['crossovered.budget.lines'].create(vals)

    @api.multi
    def action_confirm_sale(self):
        for order in self:
            if order.new_state == "sent":
                order.new_state = "presale"
        self.set_qbom_state()
        self.create_project_tmpl()
        self.create_budget_tmpl()

    @api.multi
    def action_done(self):
        return self.write({"state": "done", "new_state": "done"})

    @api.multi
    def action_unlock(self):
        self.write({"state": "sale", "new_state": "sale"})

    @api.multi
    def action_approve(self):
        for order in self:
            if order.new_state == "tobeapproved":
                # Created by ajinkya joshi on 07/10/2019
                order.new_state = "approved"

    @api.depends("order_line.product_weight")
    def _compute_weight_total(self):
        for detail in self:
            weight_tot = 0
            for line in detail.order_line:
                if line.product_id:
                    weight_tot += line.product_weight or 0.0
            detail.total_weight = weight_tot

    @api.multi
    @api.depends(
        "order_line.discount", "order_line.price_unit", "order_line.price_subtotal"
    )
    def _check_discount(self):
        for det in self:
            total_unit_price = 0
            sub_total = 0
            total_discount = 0
            if det.order_line:
                for order in det.order_line:
                    if order.price_unit != 0:
                        if order.discount:
                            total_unit_price += order.price_unit * order.product_uom_qty
                            sub_total += order.price_subtotal
                            total_discount = (
                                (total_unit_price - sub_total) / total_unit_price
                            ) * 100
                        det.total_discount_detail = total_discount
                    else:
                        raise UserError(
                            _("Please Update the Unit Price.Cannot be Zero"))

    @api.constrains("total_discount_detail")
    def _change_state(self):
        for order in self:
            if order.total_discount_detail == 0:
                order.new_state = "draft"
                order.state = 'draft'
            elif order.total_discount_detail < 10:
                order.new_state = "draft"
            elif order.total_discount_detail > 10:
                order.new_state = "tobeapproved"
            else:
                order.new_state = "draft"

    @api.multi
    def action_draft(self):
        for order in self:
            if order.total_discount_detail > 10:
                orders = self.filtered(lambda s: s.state in ["cancel", "sent"])
                return orders.write({"state": "draft", "new_state": "tobeapproved"})
            elif order.total_discount_detail < 10:
                orders = self.filtered(lambda s: s.state in ["cancel", "sent"])
                return orders.write({"state": "draft", "new_state": "draft"})
            else:
                orders = self.filtered(lambda s: s.state in ["cancel", "sent"])
                return orders.write({"state": "draft", "new_state": "draft"})


    

    @api.onchange('order_line_approve')
    def _onchange_user(self):
        # print("===++>>In")
        for order in self:
            if order.order_line_approve:
                for id in order.order_line_approve:
                    if id.users.id:
                        order.approve_flag = False




    @api.multi
    def calculate_total(self):
        total_boh_amount = 0.0
        total_moh_amount = 0.0
        total_bot_amount = 0.0 
        total_manu_amount = 0.0
        budget_amounts=''
        for order in self:
            if order.order_line:
                for i in order.order_line:
                    for j in i.qbom_ids:
                        for z in j.qbom_lines:
                            if z.boh_amt:
                                total_boh_amount += z.boh_amt
                            if z.manu_oh_amt:
                                total_moh_amount += z.manu_oh_amt
                            for h in z.product_id.route_ids: 
                                if h.name == 'Buy':
                                    if z.weight_rate*z.weight > z.purchase_price and z.weight_rate*z.weight > z.new_price_unit:
                                        total_bot_amount += z.weight_rate*z.weight
                                    else:
                                        total_bot_amount+= max(z.weight_rate* z.weight,z.purchase_price,z.new_price_unit)*z.product_qty
                                if h.name == 'Manufacture':
                                    if z.weight_rate*z.weight > z.purchase_price and z.weight_rate*z.weight > z.new_price_unit:
                                        total_manu_amount += z.weight_rate*z.weight
                                    else:
                                        total_manu_amount+= max(z.weight_rate* z.weight,z.purchase_price,z.new_price_unit)*z.product_qty
                        print('Total Manufacture Amount',total_manu_amount)
                        print('Total BOH Amount',total_boh_amount)
                        print('Total MOH Amount',total_moh_amount)
                        print('Total BOT Amount',total_bot_amount)
        if total_manu_amount:
            budget_amounts+='Total amount of manufactured Items in Quotation is '+str(total_manu_amount)+' .\n'
        if total_boh_amount:
            budget_amounts+='Total amount of BOH Items in Quotation BOM is '+str(total_boh_amount)+' .\n'
        if total_moh_amount:
            budget_amounts+='Total amount of MOH Items in Quotation BOM is '+str(total_moh_amount)+' .\n'
        if total_bot_amount:
            budget_amounts+='Total amount of Bought Out Items in Quotation BOM is '+str(total_bot_amount)+' .\n'
        if budget_amounts:
            return budget_amounts


class SaleOrderline(models.Model):
    _inherit = "sale.order.line"

    purchase_price = fields.Float(string='Cost', digits=dp.get_precision(
        'Cost Price'))
    computed_cost = fields.Float(
        string="Computed Cost", compute="set_computed_cost", store=True
    )
    qbom_ids = fields.One2many("quotation.bom", "order_line_id")
    product_category_id = fields.Many2one(
        "product.category", string="Product Category")
    quote_bom_number = fields.Integer(
        string="View Number of Quotation BOM", compute="view_quote_bom", store=True
    )
    doc_file = fields.Binary(string="Word file", attachment="True")
    filename = fields.Char("Filename")
    computed_weight = fields.Float(
        string="Reference Weight", compute="set_weight", store=True
    )
    product_weight = fields.Float("Weight (kg)",compute="_set_productweight",store=True,readonly=False)
    weight_rate = fields.Float(string="Weight Rate (Per kg)")
    schedule_ids=fields.One2many('sale.order.schedule','order_line_id')
    comp_cost = fields.Float(string="Comp Cost")
    sale_price= fields.Float(string="Sale Price (Sale Reference)",readonly=False,store=True,digits=dp.get_precision('Product Price'))
    price_unit = fields.Float('Unit Price', required=True,compute="_set_purchase_cost", readonly=False, store=True)


    @api.multi
    def _action_launch_procurement_rule(self):
        """
        This method is the entry point function for Sales Order Simulation .
        The method earlier took the quantity of from the sale_order_line but now its takes from the 
        sale_order_schedule only for which the flag (open(default),release,close) is release.
        Changes by Jeevan Gangarde March 2019.
        """
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_move', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        errors = []
        for line in self:
            for schedule_line in line.schedule_ids:
                if schedule_line.state == 'release' :
                    if line.state != 'sale' or not line.product_id.type in ('consu','product'):
                        continue
                    # qty = line._get_qty_procurement()
                    
                    # if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                    #     continue
                    # group_id=False
                    # group_id = line.order_id.procurement_group_id
                    #for schedule_line in line.schedule_lines:
                    group_id = schedule_line.procurement_group_id
                    if not group_id:
                        group_id = self.env['procurement.group'].create({
                            'name': schedule_line.order_line_id.order_id.name, 'move_type': line.order_id.picking_policy,
                            'sale_id': line.order_id.id,
                            'partner_id': line.order_id.partner_shipping_id.id,
                        })
                        schedule_line.procurement_group_id = group_id
                    else:
                        # In case the procurement group is already created and the order was
                        # cancelled, we need to update certain values of the group.
                        updated_vals = {}
                        if group_id.partner_id != line.order_id.partner_shipping_id:
                            updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                        if group_id.move_type != line.order_id.picking_policy:
                            updated_vals.update({'move_type': line.order_id.picking_policy})
                        if updated_vals:
                            group_id.write(updated_vals)

                    values = line._prepare_procurement_values(group_id=group_id)
                    values['sale_order_schedule_id']=schedule_line.id
                    product_qty = schedule_line.scheduled_qty #- qty
                    procurement_uom = line.product_uom
                    quant_uom = line.product_id.uom_id
                    get_param = self.env['ir.config_parameter'].sudo().get_param
                    if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                        product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                        procurement_uom = quant_uom
                    #for schedule_line in line.schedule_lines:
                    product_qty=0
                    if schedule_line.state=='release':
                        print("_____-----^^^--^^^-----_____")
                        product_qty=schedule_line._get_qty_procurement()
                        date_planned= datetime.datetime.strptime(schedule_line.scheduled_date, DEFAULT_SERVER_DATETIME_FORMAT)\
                    + datetime.timedelta(days=line.customer_lead or 0.0) - datetime.timedelta(days=line.order_id.company_id.security_lead)
                        values.update({
                            'date_planned' :date_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        })
                        try:
                            self.env['procurement.group'].run(schedule_line.product_id, product_qty, procurement_uom, line.order_id.partner_shipping_id.property_stock_customer, line.name, line.order_id.name, values)
                        except UserError as error:
                            errors.append(error.name)
                        
                    if errors:
                        raise UserError('\n'.join(errors))
                    else:
                        schedule_line.write({
                        'state':'close'
                        })
        return True

    # @api.onchange('doc_file')
    # def _onchange_doc_file(self):
    #     if self.filename:
    #         if (self.filename.split(".")[1] != "docx"):
    #             self.doc_file = False
    #             raise UserError(_("Please Select A Docx File"))
    
    
    
    # @api.multi
    # def unlink(self):
    #     print("UNlink Called")
    @api.depends("qbom_ids.total_weight")
    def set_weight(self):
        for order in self:
            if order.qbom_ids:
                for j in order.qbom_ids:
                    order.computed_weight = j.total_weight

    @api.depends("qbom_ids.total")
    def set_computed_cost(self):
        for order in self:
            if order.qbom_ids:
                for j in order.qbom_ids:
                    order.computed_cost = j.total

    @api.depends('computed_weight')
    def _set_productweight(self):
        for order in self:
            if order.computed_weight:
                order.product_weight = order.computed_weight 
            else:
                order.product_weight = order.product_id.weight
    # @api.onchange('computed_cost')
    # def _onchange_computedcost(self):
    #     for order in self:
    #         if order.computed_cost:
    #             order.purchase_price = order.computed_cost

    @api.multi
    def quotation_mrp_bom_new(self):
        # resume='/home/jeevan/my_projects/ResumeParser-master/resume_parser/resumes/resume.pdf'
        # resume_parser = ResumeParser(resume)
        # result= [resume_parser.get_extracted_data()]
        # print("result===============>",result)
        view = self.env.ref("quotation_bom.quotation_bom_view_form")
        context = {"default_order_line_id": self.id,
                    "default_product_category_id":self.product_id.categ_id.id,
                    "default_saleline_category":self.product_id.categ_id.id,
                    "default_saleline_product_tmpl_id":self.product_id.product_tmpl_id.id,
                    "default_saleline_product_id":self.product_id.id
        }
        return {
            "name": _("Quotation BOM"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "context": context,
            "res_model": "quotation.bom",
            "views": [(view.id, "form")],
            "view_id": view.id,
            # 'res_id': self.id,
        }
#Updated by ajinkya on 29/08/2019
    # @api.onchange("product_id")
    # def onchange_set_weight(self):
    #     if self.product_id:
           # self.product_weight = self.product_id.weight

    @api.depends("qbom_ids.order_line_id")
    def view_quote_bom(self):
        for i in self:
            if i.qbom_ids:
                nbr = 0
                for line in i.qbom_ids:
                    nbr += 1
                i.quote_bom_number = nbr

# Updated by ajinkya on 29/08/2019
    @api.depends(
        "product_uom_qty",
        "discount",
        "price_unit",
        "tax_id",
        "computed_cost",
        "product_weight",
    )
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price,
                line.order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id,
            )
            # weight_cost=line.weight*line.weight_rate
            # li.append(line.purchase_price)
            # li.append(line.new_price_unit)
            # li.append(weight_cost)
            # max_cost=max(li)
            # li=[]
            line.update(
                {
                    "price_tax": sum(
                        t.get("amount", 0.0) for t in taxes.get("taxes", [])
                    ),
                    "price_total": taxes["total_included"],
                    "price_subtotal": taxes['total_excluded']
                }
            )

    # @api.onchange('product_category_id')
    # def onchng_set_prod_template(self):
    #     for line in self:
    #         li = []
    #         domain = {}
    #         if line.product_category_id:
    #             self.product_tmpl_id=False
    #             self.product_id = False
    #             prod_tmpls = line.env['product.template'].search(
    #                 [('categ_id', '=', line.product_category_id.id)])
    #             for prod_tmpl in prod_tmpls:
    #                 li.append(prod_tmpl.id)
    #             domain['product_tmpl_id'] = [('id', 'in', li)]
    #         return {'domain': domain}
    # Updated by ajinkya on 29/08/2019
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['sale_price'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        return result

# Updated by ajinkya on 29/08/2019
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.sale_price = 1.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.sale_price = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)


# Updated by ajinkya on 29/08/2019
    def _get_protected_fields(self):
        return [
            'product_id', 'name', 'sale_price', 'product_uom', 'product_uom_qty',
            'tax_id', 'analytic_tag_ids'
        ]

# Updated by ajinkya on 29/08/2019
    @api.onchange('product_id', 'sale_price', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and self.order_id.pricelist_id and
                self.order_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('sale.group_discount_per_so_line')):
            return

        self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order, uom=self.product_uom.id)

        price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        new_list_price, currency_id = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.order_id.pricelist_id.id)

        if new_list_price != 0:
            if self.order_id.pricelist_id.currency_id.id != currency_id:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(new_list_price, self.order_id.pricelist_id.currency_id)
            discount = (new_list_price - price) / new_list_price * 100
            if discount > 0:
                self.discount = discount       

# Updated by ajinkya on 29/08/2019

    @api.depends('computed_cost')
    def _set_purchase_cost(self):
        for order in self:
            if order.computed_cost:
                # print("computed cost",order.computed_cost)
                order.price_unit = order.computed_cost
                # print("Price Unit",order.price_unit)
            else:
                order.price_unit = 1.0

    @api.onchange('product_id')
    def _check_category(self):
        if self.product_category_id != self.product_id.categ_id:
            self.product_category_id = self.product_id.categ_id

    class approve_info(models.Model):
        _name = "approval.info"

        users = fields.Many2one("res.users", required=True)
        approve_status = fields.Boolean("Approval Status")
        order_approve_id = fields.Many2one("sale.order")
        text = fields.Char("Comment")
