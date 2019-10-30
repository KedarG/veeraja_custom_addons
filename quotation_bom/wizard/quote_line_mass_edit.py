from odoo import api, fields, models


class QuoteLineMassEdit(models.TransientModel):
    _name = 'quoteline.massedit'
    _description = 'Quote Line Mass Edit'

    moh = fields.Float(string='MOH(%)')
    boh = fields.Float(string='BOH(%)')
    margin = fields.Float(string='Margin(%)')
    weight_rate = fields.Float(string="Wt. Rate / kg")
    @api.multi
    def mass_update(self):
        active_ids = self.env.context['active_ids']
        #print("active_ids==============>", active_ids)
        for i in active_ids:
            quote_line_obj = self.env['quotation.bom.line'].browse(i)
            if self.boh:
                quote_line_obj.bo_oh = self.boh
            if self.moh:
                quote_line_obj.manufacture_oh = self.moh
            if self.margin:
                quote_line_obj.margin = self.margin
            if self.weight_rate:
                quote_line_obj.weight_rate = self.weight_rate
