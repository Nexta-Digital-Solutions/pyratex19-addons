# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          help="The analytic account related to this purchase order.")

