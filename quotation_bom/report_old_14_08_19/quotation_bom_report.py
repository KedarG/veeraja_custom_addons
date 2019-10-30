from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
import locale
from num2words import num2words
from collections import OrderedDict 


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'  

class QuotationDetailReport(models.Model):
    _inherit = 'quotation.bom'

    @api.multi
    def set_amt(self,amt):
        locale.setlocale(locale.LC_ALL, '')
        return locale.format("%.2f", amt, grouping=True)

    @api.multi
    def set_amt_in_text(self,amount):
        for curr_id in self:
            split_num=str(amount).split('.')
            int_part=int(split_num[0])
            decimal_part=int(split_num[1])
            fld=0.00
            amt=0
            flagdecima=0.00
            amt,fld=divmod(amount,1)
            flagdecima= fld*100
            temp="{:.0f}".format(flagdecima)
            a=int(temp)
            amountinwordf=num2words(amt,lang='en_IN').replace(',', ' ').title()
            amountinwords=num2words(a,lang='en_IN').replace(',', ' ').title()
            finalamount=amountinwordf+' and '+ amountinwords + "\t"+curr_id.currency_id.currency_subunit_label +"\t"+"Only"
            return finalamount

class QuotationDetailLineReport(models.Model):
    _inherit = 'quotation.bom.line'

    @api.multi
    def caculate_igst(self):
          pairs=[]
          igst_val={}
          for tax in self:
             for i in tax.tax_id:
                if i.tax_group_id.name=='IGST':
                    sum_tax=((i.amount)*tax.price_subtotal)/100
                    igst_val['sum_tax']=sum_tax
                    igst_val['desc']=i.description
                    pairs.append((i.description,sum_tax))
          sums = {}
          for pair in pairs:
            sums.setdefault(pair[0], 0)
            sums[pair[0]] += pair[1]
          return sums.items()
        
    @api.multi
    def calculate_cgst_sgst(self): 
        sgst={}
        pairs=[]
        for tax in self:
            for i in tax.tax_id.children_tax_ids:
                sum_tx=((i.amount)*tax.price_subtotal)/100
                sgst['sum_tx']=sum_tx
                sgst['description']=i.description
                pairs.append((i.description,sum_tx))
        sums = OrderedDict()
        for pair in pairs:
              sums.setdefault(pair[0], 0)
              sums[pair[0]] += pair[1]

        return sums.items()
         
    @api.multi
    def sgst_calculate(self):
        for tax in self:
            for children_id in tax.tax_id.children_tax_ids:
                if children_id.tax_group_id.name=="SGST":   
                    line_cgst_tax=((children_id.amount)*(tax.price_subtotal))/100
                    return line_cgst_tax
          


