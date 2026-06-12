# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.http import request

class Website(models.Model):
    _inherit = 'website'
    
    def sale_get_order(self, *args, **kwargs):
        if (kwargs.get('update_pricelist')):
            kwargs.update({ 'update_pricelist': False})
        so = super().sale_get_order(*args, **kwargs)
        return so.with_context(warehouse=so.warehouse_id.id) if so else so

    def _prepare_sale_order_values(self, partner_sudo):
        self.ensure_one()
        if request.get('update_pricelist'):
            request.pricelist = False
        return super(Website, self)._prepare_sale_order_values(partner_sudo)
