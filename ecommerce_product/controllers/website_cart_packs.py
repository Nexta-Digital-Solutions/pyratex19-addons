# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class clearCartAllProducts(http.Controller):

    @http.route(['/shop/clear/cart'], type='http', auth="public", website=True, sitemap=False)
    def clear_cart(self, **kwargs):
        """Elimina del carrito las líneas de muestras (Swatches).

        Odoo 19: el carrito se obtiene con request.cart (request._create_cart()
        ya no existe).
        """
        order_sudo = request.cart
        if order_sudo:
            order_sudo.order_line.filtered(
                lambda line: line.product_id.producttype_id.name == 'Swatches'
            ).unlink()
        return request.redirect("/shop/cart")
