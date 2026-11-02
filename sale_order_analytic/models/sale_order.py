# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare

import logging

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import groupby

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        # Un fallo al crear la cuenta analítica no debe impedir la confirmación del pedido
        # (en el pago web el error se traga y el pedido quedaba sin confirmar).
        for order in self:
            try:
                with self.env.cr.savepoint():
                    order._set_analytic_account_on_lines()
            except Exception:
                _logger.exception(
                    "No se pudo crear la cuenta analítica del pedido %s", order.name)
        return res

    def _set_analytic_account_on_lines(self):
        self.ensure_one()
        lines = self.order_line.filtered(lambda l: not l.analytic_distribution)
        if not lines:
            return
        plan = self.env['account.analytic.plan'].sudo().search(
            [('name', 'ilike', 'Default')], limit=1)
        if not plan:
            plan = self.env['account.analytic.plan'].sudo().search([], limit=1)
        if not plan:
            _logger.warning("No hay plan analítico: pedido %s sin cuenta analítica", self.name)
            return
        account = self.env['account.analytic.account'].sudo().create({
            'name': self.name,
            'partner_id': self.partner_id.id,
            'plan_id': plan.id,
            'company_id': self.company_id.id,
        })
        lines.write({'analytic_distribution': {str(account.id): 100}})
