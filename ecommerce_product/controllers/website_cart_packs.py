# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

class clearCartAllProducts(http.Controller):
    
    @http.route(['/shop/clear/cart'], type='http', auth="public", website=True)
    def clear_cart(self, **kwargs):
        order = request.website.sale_get_order(force_create=1)
        order_line = request.env['sale.order.line'].sudo()
        line_ids = order_line.search([('order_id', '=', order.id)])
        for line in line_ids:
            line_obj = order_line.browse([int(line)])
            if line_obj and line_obj.product_id.producttype_id.name == 'Swatches':
                line_obj.unlink()
        return request.redirect("/shop/cart")
        