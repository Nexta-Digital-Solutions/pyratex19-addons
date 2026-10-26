# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare

from odoo import api, fields, models, SUPERUSER_ID, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_vendor_bill_id = fields.Many2one(
        'account.move',
        store=True,
        check_company=True,
        string='Vendor Bill',
        help="Auto-complete from a previous bill or refund.",
    )
