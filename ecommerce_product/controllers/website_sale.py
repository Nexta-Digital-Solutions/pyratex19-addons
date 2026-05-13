# -*- coding: utf-8 -*-

from collections import defaultdict
from itertools import product as cartesian_product
import json
import logging
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.urls import url_decode, url_encode, url_parse

from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.fields import Command
from odoo.http import request
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.ecommerce_filter.controllers.website_sale_products import ProductsFilter
from odoo.addons.payment import utils as payment_utils
from odoo.tools.json import scriptsafe as json_scriptsafe

_logger = logging.getLogger(__name__)

class WebsiteSaleProducts(ProductsFilter):
    
    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True,
        product_custom_attribute_values=None, no_variant_attribute_values=None, price_unit = None,**kw
    ):
        order = request.website.sale_get_order(force_create=True)
        if order.state != 'draft':
            request.website.sale_reset()
            if kw.get('force_create'):
                order = request.website.sale_get_order(force_create=True)
            else:
                return {}

        if product_custom_attribute_values:
            product_custom_attribute_values = json_scriptsafe.loads(product_custom_attribute_values)

        if no_variant_attribute_values:
            no_variant_attribute_values = json_scriptsafe.loads(no_variant_attribute_values)

        values = order.sudo()._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            **kw
        )
        
        self.setTypeofOrder(order, set_qty, add_qty)
        
        if (price_unit ):
            line_id = request.env['sale.order.line'].sudo().browse(values['line_id'])
            line_id.sudo().update ({
                'price_unit': price_unit,
            })       
        
        request.session['website_sale_cart_quantity'] = order.cart_quantity

        if not order.cart_quantity:
            request.website.sale_reset()
            return values

        open_pack = request.env['product.product'].sudo().search([('name', '=', 'Open Pack')], limit=1)

        if open_pack and product_id == open_pack.id and (set_qty == 0 or (add_qty and values['quantity'] == 0)):
            open_swatches_lines = order.order_line.filtered(lambda l: l.product_id.producttype_id.name == "Swatches" and not l.pack_parent_line_id)
            for line in open_swatches_lines:
                line.unlink()

        all_closed_packs = request.env['product.product'].sudo().search([('pack_ok', '=', True)])

        product = request.env['product.product'].sudo().browse(product_id)
        # CORRECTO ID 11145
        _logger.error(f'ID DEL PRODUCTO: {product}')

        closed_pack = order.order_line.filtered(lambda l: l.product_id.pack_ok == True)
        _logger.error(f'CLOSED PACK: {closed_pack.name}')
        _logger.error(f'CLOSED PACK: {closed_pack.product_id}')

        if product in all_closed_packs and (set_qty == 0 or (add_qty and values['quantity'] == 0)):
            closed_swatches_lines = order.order_line.filtered(lambda l: l.product_id.producttype_id.name == "Swatches")

            for line in closed_swatches_lines:
                line.unlink()


        request.session['website_sale_cart_quantity'] = order.cart_quantity

        values['cart_quantity'] = order.cart_quantity
        values['minor_amount'] = payment_utils.to_minor_currency_units(
            order.amount_total, order.currency_id
        ),
        values['amount'] = order.amount_total

        if not display:
            return values

        values['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template(
            "website_sale.cart_lines", {
                'website_sale_order': order,
                'date': fields.Date.today(),
                'suggested_products': order._cart_accessories()
            }
        )
        values['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template(
            "website_sale.short_cart_summary", {
                'website_sale_order': order,
            }
        )
        
        """
        if (line_id):
            values.update ({ 'website_sale_order': order })
            self.addPercentageProductFabric(values, order.cart_quantity)
            values['amount'] = order.cart_quantity * order.amount_total
        """
        return values
    
    @http.route(['/shop/cart'], type='http', auth="public", website=True, sitemap=False)
    def cart(self, access_token=None, revive='', **post):
        """
        Main cart management + abandoned cart revival
        access_token: Abandoned cart SO access token
        revive: Revival method when abandoned cart. Can be 'merge' or 'squash'
        """
        order = request.website.sale_get_order()
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.website.sale_get_order()

        request.session['website_sale_cart_quantity'] = order.cart_quantity

        values = {}
        if access_token:
            abandoned_order = request.env['sale.order'].sudo().search([('access_token', '=', access_token)], limit=1)
            if not abandoned_order:  # wrong token (or SO has been deleted)
                raise NotFound()
            if abandoned_order.state != 'draft':  # abandoned cart already finished
                values.update({'abandoned_proceed': True})
            elif revive == 'squash' or (revive == 'merge' and not request.session.get('sale_order_id')):  # restore old cart or merge with unexistant
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/shop/cart')
            elif revive == 'merge':
                abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session.get('sale_order_id'):  # abandoned cart found, user have to choose what to do
                values.update({'access_token': abandoned_order.access_token})

        values.update({
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': [],
        })
        if order:
            values.update(order._get_website_sale_extra_values())
            order.order_line.filtered(lambda l: l.product_id and not l.product_id.active).unlink()
            values['suggested_products'] = order._cart_accessories()
            values.update(self._get_express_shop_payment_values(order))
            
            self. setTypeofOrder(order, order.cart_quantity, 0)
            #self.addPercentageProductFabric(values)

        if post.get('type') == 'popover':
            # force no-cache so IE11 doesn't cache this XHR
            return request.render("website_sale.cart_popover", values, headers={'Cache-Control': 'no-cache'})

        return request.render("website_sale.cart", values)
    
    def addPercentageProductFabric(self, values, qty = False):
        order = values.get('website_sale_order')
        percentage_additional = int(request.env['ir.config_parameter'].sudo().get_param('Fabric Percentage', 1))
        for line in order.order_line:
            if line.product_id.categ_id.parent_id.name and (not line.check_price or qty):
                if (line.product_id.categ_id.parent_id.name.lower() == "fabric" and 
                    self.user_has_groups('base.group_portal')):
                    tax = line.tax_id.amount
                    price_unit = line.price_unit * (1 + percentage_additional / 100)
                    price_reduce = price_unit
                    price_reduce_taxinc = price_unit * (1 + tax /100 )
                    line.update ({
                        'price_unit': price_unit,
                        'price_reduce': price_reduce_taxinc,
                        'price_tax': float(price_reduce_taxinc - price_unit),
                        'price_subtotal': float(price_unit),
                        'price_reduce_taxinc': price_reduce_taxinc,
                        'price_total': line.product_qty * price_reduce_taxinc,
                        'check_price': True
                    })
                    
    def setTypeofOrder(self, order, set_qty, add_qty):
        """type_of_order: prevalece el de fabrics"""
        saleorder_line_ids = order.order_line if order.order_line else False
        if (saleorder_line_ids and ((set_qty  and set_qty > 0 ) or (add_qty and add_qty > 0))):
            type_of_order_fabrics = saleorder_line_ids.filtered(lambda x: isinstance(x.product_id.product_tmpl_id.producttype_id.name, str)
            and x.product_id.product_tmpl_id.producttype_id.name.lower() == "fabrics")
            type_of_order = type_of_order_fabrics[0].product_id.product_tmpl_id.producttype_id.type_of_order \
                            if type_of_order_fabrics else saleorder_line_ids[0].product_id.product_tmpl_id.producttype_id.type_of_order if  order.order_line else False
           
            type_of_order_current = type_of_order if not order.x_studio_type_of_order else order.x_studio_type_of_order
            type_of_order_fabrics = request.env['product.type'].sudo().search([ ('name','=','Fabrics') ], limit = 1).type_of_order
            if (type_of_order_current == type_of_order_fabrics 
                and type_of_order !=  type_of_order_fabrics):
                type_of_order = type_of_order_fabrics
            order.update({
                'x_studio_type_of_order': type_of_order 
            })
           
           
    @http.route(['/shop/cart/getOpenPackCount'], type='json', auth="user", methods=['POST'], website=True, csrf=False)
    def getOpenPackCount(self, **kw):
        order = request.website.sale_get_order(force_create=False)
        is_openPack = True if order.order_line.filtered(lambda x: x.product_id.name == 'Open Pack') else False
        return is_openPack
        
         
