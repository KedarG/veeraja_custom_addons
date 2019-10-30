# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"

    date_from = fields.Date('Start Date', required=False, states={
                            'done': [('readonly', True)]})
    date_to = fields.Date('End Date', required=False, states={
                          'done': [('readonly', True)]})
    budget_amount = fields.Text(name="Reference Amounts")


class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'
    date_from = fields.Date('Start Date', required=False)
    date_to = fields.Date('End Date', required=False)
    theoritical_amount = fields.Float(
        compute='_compute_theoritical_amount', string='Theoretical Amount', digits=0)

    @api.multi
    def _compute_theoritical_amount(self):
        return 0.0

    @api.multi
    def _compute_practical_amount(self):
        for line in self:
            result = 0.0
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = self.env.context.get(
                'wizard_date_to') or line.date_to if line.date_to else False
            date_from = self.env.context.get(
                'wizard_date_from') or line.date_to if line.date_to else False
            if date_to and date_from:
                if line.analytic_account_id.id:
                    self.env.cr.execute("""
                        SELECT SUM(amount)
                        FROM account_analytic_line
                        WHERE account_id=%s
                            AND (date between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))
                            AND general_account_id=ANY(%s)""",
                                        (line.analytic_account_id.id, date_from, date_to, acc_ids,))
                    result = self.env.cr.fetchone()[0] or 0.0
            else:
                if line.analytic_account_id.id:
                    self.env.cr.execute("""
                        SELECT SUM(amount)
                        FROM account_analytic_line
                        WHERE account_id=%s
                            AND general_account_id=ANY(%s)""",
                                        (line.analytic_account_id.id, acc_ids,))
                    result = self.env.cr.fetchone()[0] or 0.0
            line.practical_amount = result
