# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'
    
    def sale_get_order(self, *args, **kwargs):
        if (kwargs.get('update_pricelist')):
            kwargs.update({ 'update_pricelist': False})
        so = super().sale_get_order(*args, **kwargs)
        return so.with_context(warehouse=so.warehouse_id.id) if so else so