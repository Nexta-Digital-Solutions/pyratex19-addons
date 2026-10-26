# -*- coding: utf-8 -*-
"""Rutas JSON para el "Open Pack", reescritas para Odoo 19.

Sustituyen a la antigua `/shop/cart/update_json` (usaba `sale.order._cart_update`,
que ya no existe en Odoo 19) y a `/shop/cart/getOpenPackCount`.

El precio del pack se toma del registro `open.pack` en el servidor, en lugar de
recibirlo desde el navegador.
"""
from odoo import _, http
from odoo.http import request

OPEN_PACK_PRODUCT_NAME = 'Open Pack'


class OpenPackCart(http.Controller):

    def _get_open_pack_product(self):
        return request.env['product.product'].sudo().search(
            [('name', '=', OPEN_PACK_PRODUCT_NAME)], limit=1
        )

    def _cart_has_open_pack(self, order_sudo, open_pack_product):
        return bool(order_sudo and order_sudo.order_line.filtered(
            lambda line: line.product_id == open_pack_product
        ))

    @http.route(
        '/shop/cart/open_pack/exists', type='jsonrpc', auth='user',
        methods=['POST'], website=True, sitemap=False,
    )
    def open_pack_exists(self, **kwargs):
        return self._cart_has_open_pack(request.cart, self._get_open_pack_product())

    @http.route(
        '/shop/cart/open_pack/add', type='jsonrpc', auth='user',
        methods=['POST'], website=True, sitemap=False,
    )
    def open_pack_add(self, pack_id, product_template_ids, **kwargs):
        pack = request.env['open.pack'].sudo().browse(int(pack_id)).exists()
        if not pack:
            return {'error': 'pack_not_found', 'message': _("The selected pack does not exist.")}

        template_ids = [int(tmpl_id) for tmpl_id in product_template_ids or []]
        if not template_ids:
            return {'error': 'empty_pack', 'message': _("Add at least one product to the pack.")}
        if pack.elements_number and len(template_ids) > pack.elements_number:
            return {
                'error': 'too_many_products',
                'message': _("This pack accepts at most %s products.", pack.elements_number),
            }

        open_pack_product = self._get_open_pack_product()
        if not open_pack_product:
            return {'error': 'open_pack_missing', 'message': _("Customized Swatch not found")}

        order_sudo = request.cart or request.website._create_cart()
        if self._cart_has_open_pack(order_sudo, open_pack_product):
            return {'error': 'pack_already_in_cart', 'cart_quantity': order_sudo.cart_quantity}

        templates = request.env['product.template'].sudo().browse(template_ids).exists()
        templates_by_id = {template.id: template for template in templates}
        lines_to_add = [(open_pack_product, pack.price)]
        for tmpl_id in template_ids:
            variant = templates_by_id.get(tmpl_id, request.env['product.template']).product_variant_id
            if variant:
                lines_to_add.append((variant, 0.0))

        cart = order_sudo.with_context(skip_cart_verification=True)
        for product, price_unit in lines_to_add:
            values = cart._cart_add(product_id=product.id, quantity=1)
            line = order_sudo.order_line.filtered(lambda sol: sol.id == values.get('line_id'))
            if line:
                # En Odoo 19 un price_unit distinto de technical_price_unit se
                # considera precio manual y no se recalcula automáticamente.
                line.price_unit = price_unit

        order_sudo._verify_cart_after_update()

        request.env['user.open.pack'].sudo().search(
            [('user_id', '=', request.env.uid)]
        ).unlink()

        return {'cart_quantity': order_sudo.cart_quantity}
