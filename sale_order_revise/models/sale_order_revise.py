from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = "sale.order"

    revise_order_checkbox = fields.Boolean('Revise Qutation')
    sale_line = fields.One2many("sale.order.revise", 'sale_id')
    revise_count = fields.Integer("Revise Count")
    revise_name = fields.Char("name", readonly=True, store=True)

    # To check on confirm sale button item has bom or not(if item has bom not created then it will not confirm sale order)

    @api.multi
    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))
        self._action_confirm()
        for order in self:
            order.create_revision()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True

    # On save button write method will call and create revision order for sales(Revise Sales Order)

    @api.multi
    def write(self, vals):
        if "revise_order_checkbox" in vals:
            if vals["revise_order_checkbox"] == True:
                self.create_revision()
                self.revise_count = self.revise_count + 1
                self.revise_name = "REV-" + (str(self.revise_count))
                vals["revise_order_checkbox"] = False
        variable = super(SaleOrder, self).write(vals)
        return variable

    # Here Create Revision Of Order and Order_Line in as sale_order_revise and sale_order_line_revise

    @api.multi
    def create_revision(self):
        revision_vals = {
            'revise_name': self.revise_name,
            'sale_id': self.id,
            'name': self.name,
            'partner_id': self.partner_id.id,
            'validity_date': self.validity_date,
            'payment_term_id': self.payment_term_id.id,
            'user_id': self.user_id and self.user_id.id,
            'client_order_ref': self.client_order_ref,
            'team_id': self.team_id.id,
            'date_order': self.date_order,
            'fiscal_position_id': self.fiscal_position_id.id,
            'origin': self.origin,
            'margin': self.margin,
            'partner_invoice_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'pricelist_id': self.pricelist_id.id,
            'amount_untaxed': self.amount_untaxed,
            'amount_tax': self.amount_tax,
            'amount_total': self.amount_total
        }
        sale_order_revise_obj = self.env['sale.order.revise'].create(
            revision_vals)
        sale_order_revise_obj.sale_id = self.id
        categ_id = 0
        for i in self.order_line:
            if i.layout_category_id.id:
                categ_id = i.layout_category_id.id
            line_rivision_vals = {
                'sale_orderrevise_id': sale_order_revise_obj.id,
                'layout_category_id': categ_id,
                'discount': i.discount,
                'product_id': i.product_id.id,
                'name': i.name,
                'product_uom_qty': i.product_uom_qty,
                'price_unit': i.price_unit,
                'tax_id': i.tax_id,
                'price_subtotal': i.price_subtotal,
                'order_id': self.id,
                'product_uom': i.product_uom,
                'purchase_price': i.purchase_price
            }
            sale_order_revise_obj.sale_orderlinerevise_line = [
                (0, 0, line_rivision_vals)]
            sale_order_revise_obj.sale_id = self.id


class SaleOrderRevise(models.Model):
    _name = "sale.order.revise"

    revise_name = fields.Char(
        "Sale Order Revise Count", readonly=True, store=True)
    sale_id = fields.Many2one("sale.order")
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    sale_orderlinerevise_line = fields.One2many(
        "sale.order.line.revise", 'sale_orderrevise_id')
    margin = fields.Monetary(
        help="It gives profitability by calculating the difference between the Unit Price and the cost.", store=True)
    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={
                       'draft': [('readonly', False)]}, index=True, default=lambda self: ('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)], 'sent': [
                                 ('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always')
    validity_date = fields.Date(string='Expiration Date', readonly=True, copy=False, states={'draft': [('readonly', False)], 'sent': [(
        'readonly', False)]}, help="Manually set the expiration date of your quotation (offer), or it will set the date automatically based on the template if online quotation is installed.", store=True)
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', oldname='payment_term', store=True)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True,
                              track_visibility='onchange', default=lambda self: self.env.user)
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    team_id = fields.Many2one(
        'crm.team', 'Sales Channel', change_default=True, oldname='section_id')
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True, states={
                                 'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', oldname='fiscal_position', string='Fiscal Position')
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that generated this sales order request.")
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=True, required=True, states={
                                         'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Invoice address for current sales order.", store=True)
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True, states={
                                          'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Delivery address for current sales order.", store=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True, states={
                                   'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order.")
    currency_id = fields.Many2one(
        "res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)
    amount_untaxed = fields.Monetary('Untaxed Amount', store=True)
    amount_tax = fields.Monetary('Taxes', store=True)
    amount_total = fields.Monetary('Total', store=True)


class SaleOrderLineRevise(models.Model):
    _name = "sale.order.line.revise"

    sale_orderrevise_id = fields.Many2one("sale.order.revise")
    layout_category_id = fields.Many2one(
        'sale.layout_category', string='Section', store=True)
    discount = fields.Float(string='Discount (%)', default=0.0, store=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[(
        'sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True, store=True)
    name = fields.Text(string='Description', required=True, store=True)
    product_uom_qty = fields.Float(
        string='Quantity', required=True, default=1.0, store=True)
    price_unit = fields.Float(
        'Unit Price', required=True, default=0.0, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=[
                              '|', ('active', '=', False), ('active', '=', True)], store=True)
    order_id = fields.Many2one('sale.order', string='Order Reference',
                               required=True, ondelete='cascade', index=True, copy=False, store=True)
    currency_id = fields.Many2one(
        related='order_id.currency_id', store=True, string='Currency', readonly=True)
    price_subtotal = fields.Monetary('Subtotal', store=True)
    product_uom = fields.Many2one(
        "product.uom", string='Unit Price', store=True)
    purchase_price = fields.Float(
        string='Cost', digits=dp.get_precision('Product Price'))
