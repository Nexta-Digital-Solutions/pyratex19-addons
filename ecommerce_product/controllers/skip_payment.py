# -*- coding: utf-8 -*-
"""Confirmación del pedido web sin pago (portado del módulo OCA
website_sale_checkout_skip_payment de v16, que no está instalado en v19).

Para los clientes con `skip_website_checkout_payment`, /shop/confirmation
confirma el pedido (Delivery Order, factura según configuración), envía el correo
de confirmación y muestra la página de confirmación estándar.
"""
import logging

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.payment import PaymentPortal

_logger = logging.getLogger(__name__)


class CheckoutSkipPayment(PaymentPortal):

    @http.route()
    def shop_payment_confirmation(self, **post):
        if not request.website.checkout_skip_payment:
            return super().shop_payment_confirmation(**post)

        order = request.cart
        if order and order.state == 'draft' and order.order_line:
            order = order.sudo()
            order.action_confirm()
            try:
                order.with_context(mark_so_as_sent=True)._send_order_confirmation_mail()
            except Exception:
                _logger.exception(
                    "Error enviando el correo de confirmación del pedido %s", order.name)
            request.session['sale_last_order_id'] = order.id
            request.website.sale_reset()
        elif request.session.get('sale_last_order_id'):
            pass  # recarga de la página de confirmación
        else:
            return request.redirect('/shop')
        return super().shop_payment_confirmation(**post)
