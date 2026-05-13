# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.stock.models.stock_rule import ProcurementException
from odoo.tools import groupby

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if not self.analytic_account_id:
            company_id = self.company_id
            plan_id = self.env['account.analytic.plan'].search([('name','ilike', 'Default'), ('company_id','=', company_id.id)])
            if not plan_id:
                plan_id = self.env['account.analytic.plan'].search(
                    [('name', 'ilike', 'Default'), ('company_id', '=', False)])
            new_analytic_account_id = self.env['account.analytic.account'].create({
                'name': self.name,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'plan_id': plan_id[0].id if plan_id else False,
            })
            if bool(new_analytic_account_id):
                self.update({
                    'analytic_account_id': new_analytic_account_id.id
                })
        return res
