from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website_sale_delivery.controllers.main import WebsiteSaleDelivery as ws
from odoo import fields, http, SUPERUSER_ID, tools, _
from datetime import datetime
from werkzeug.exceptions import NotFound
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.tools import lazy


class ProductsFilter(ws, TableCompute, http.Controller):

    def _get_search_options(
            self, category=None, product=None, attrib_values=None, pricelist=None, min_price=0.0, max_price=0.0, conversion_rate=1,
            **post
    ):
        product_available_meters = False
        if post.get('availablemeters', False):
            avail_meters = request.env['product.available.meters'].sudo().search([('id', '=', int(post.get('availablemeters')))])
            product_available_meters = request.env['product.template'].sudo().search(
            [('virtual_available', '<=', avail_meters.max), ('virtual_available', '>=', avail_meters.min)])
        res = {
            'displayDescription': True,
            'displayDetail': True,
            'displayExtraDetail': True,
            'displayExtraLink': True,
            'displayImage': True,
            'allowFuzzy': not post.get('noFuzzy'),
            'category': str(category.id) if category else None,
            'product': str(product.id) if product else None,
            'min_price': min_price / conversion_rate,
            'max_price': max_price / conversion_rate,
            'attrib_values': attrib_values,
            'display_currency': pricelist.currency_id,
            'fiberfamily': post.get('fiberfamily', False),
            'colorgroup': post.get('colorgroup', False),
            'structure': post.get('structure', False),
            'property': post.get('property', False),
            'usage': post.get('usage', False),
            'availablemeters': product_available_meters.ids if product_available_meters else False,
            'producttype': post.get('producttype', False),
            'careinstructions': post.get('careinstructions', False),
            'certification': post.get('certification', False),
        }

        return res

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
        '/shop/product/<model("product.template"):product>'
    ], type='http', auth="public", website=True, sitemap=ws.sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, product=None, **post):
        add_qty = int(post.get('add_qty', 1))
        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 0

        Category = request.env['product.public.category']
        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        website = request.env['website'].get_current_website()
        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = website.shop_ppg or 20

        ppr = website.shop_ppr or 4

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        fiberfamily_set = False
        if post.get('fiberfamily'):
            fiberfamily_set = int(post.get('fiberfamily', False))
        colorgroup_set = False
        if post.get('colorgroup'):
            colorgroup_set = int(post.get('colorgroup', False))
        structure_set = False
        if post.get('structure'):
            structure_set = int(post.get('structure', False))
        property_set = False
        if post.get('property'):
            property_set = int(post.get('property', False))
        usage_set = False
        if post.get('usage'):
            usage_set = int(post.get('usage', False))
        availablemeters_set = False
        if post.get('availablemeters', False):
            availablemeters_set = request.env['product.available.meters'].search([ ('id', '=',  int(post.get('availablemeters'))) ])
            
        producttype_set = producttype_set_not_swatches = False
        if post.get('producttype'):
            producttype_set = int(post.get('producttype', False))
            producttype_set_not_swatches = not bool (request.env['product.type'].sudo().search( [ ('name', 'ilike', 'swatches%'), ('id','=', producttype_set)], limit = 1))
        careinstructions_set = False
        if post.get('careinstructions'):
            careinstructions_set = int(post.get('careinstructions', False))
        certification_set = False
        if post.get('certification'):
            certification_set = int(post.get('certification', False))

        keep = QueryURL('/shop',
                        **self._shop_get_query_url_kwargs(category and int(category), search, min_price, max_price,
                                                          **post))

        now = datetime.timestamp(datetime.now())
        pricelist = request.env['product.pricelist'].browse(request.session.get('website_sale_current_pl'))
        if not pricelist or request.session.get('website_sale_pricelist_time',
                                                0) < now - 60 * 60:  # test: 1 hour in session
            pricelist = website.get_current_pricelist()
            request.session['website_sale_pricelist_time'] = now
            request.session['website_sale_current_pl'] = pricelist.id

        request.update_context(pricelist=pricelist.id, partner=request.env.user.partner_id)

        filter_by_price_enabled = website.is_view_active('website_sale.filter_products_price')
        if filter_by_price_enabled:
            company_currency = website.company_id.currency_id
            conversion_rate = request.env['res.currency']._get_conversion_rate(
                company_currency, pricelist.currency_id, request.website.company_id, fields.Date.today())
        else:
            conversion_rate = 1

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        options = self._get_search_options(
            category=category,
            attrib_values=attrib_values,
            pricelist=pricelist,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post
        )
        fuzzy_search_term, product_count, search_product = self._shop_lookup_products(attrib_set, options, post, search,
                                                                                      website)
        if colorgroup_set:
            search_product = search_product.filtered(lambda template: template.product_variant_ids.filtered(
                lambda product: colorgroup_set in product.mapped(
                    'product_template_attribute_value_ids.product_attribute_value_id.colorgroup_id.id') and product.is_published))
            product_count = len(search_product)
        filter_by_price_enabled = website.is_view_active('website_sale.filter_products_price')
        if filter_by_price_enabled:
            # TODO Find an alternative way to obtain the domain through the search metadata.
            Product = request.env['product.product'].with_context(bin_size=True)
            domain = self._get_search_domain(search, category, attrib_values)

            # This is ~4 times more efficient than a search for the cheapest and most expensive products
            from_clause, where_clause, where_params = Product._where_calc(domain).get_sql()
            query = f"""
                    SELECT COALESCE(MIN(list_price), 0) * {conversion_rate}, COALESCE(MAX(list_price), 0) * {conversion_rate}
                      FROM {from_clause}
                     WHERE {where_clause}
                """
            request.env.cr.execute(query, where_params)
            available_min_price, available_max_price = request.env.cr.fetchone()

            if min_price or max_price:
                # The if/else condition in the min_price / max_price value assignment
                # tackles the case where we switch to a list of products with different
                # available min / max prices than the ones set in the previous page.
                # In order to have logical results and not yield empty product lists, the
                # price filter is set to their respective available prices when the specified
                # min exceeds the max, and / or the specified max is lower than the available min.
                if min_price:
                    min_price = min_price if min_price <= available_max_price else available_min_price
                    post['min_price'] = min_price
                if max_price:
                    max_price = max_price if max_price >= available_min_price else available_max_price
                    post['max_price'] = max_price

        website_domain = website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search(
                [('product_tmpl_ids', 'in', search_product.ids)] + website_domain
            ).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
            search_product = request.env['product.template'].search([ '|',('name', 'ilike', search),
                                                                      ('default_code', 'ilike', search)])
            product_count = len(search_product.ids)
        else:
            search_categories = Category
        categs = lazy(lambda: Category.search(categs_domain))

        if category:
            url = "/shop/category/%s" % slug(category)

        pager = website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset:offset + ppg]

        """Mostrar solo product.template que tiene por lo menos una variante publicada """
        """ ademas si se filtra por los metros, mira en el almacen correspondiente y entonces si cumple el filtro
            se mostrara sino no"""
        products_with_variants = []
        location_id = request.env['stock.location'].sudo().search( [ ('name', '=', 'Spain/External Warehouse') ])

       
        products = search_product 
        if not producttype_set:
            for product in products:
                for product_variant in product.product_variant_ids:
                    if (product_variant.is_published ):
                        #and product_variant.producttype_id.name and product_variant.producttype_id.name.lower() !="swatches"):
                            products_with_variants.append(product.id)
            products = products.search([ ('id','in',products_with_variants) ])
        #elif producttype_set_not_swatches:
        else:
            for product in products:
                for product_variant in product.product_variant_ids:
                    if (product_variant.is_published == True):
                        if (not availablemeters_set):
                            products_with_variants.append(product.id)
                        else:
                            stock_product_variant = request.env['product.product'].sudo().search([ ('id', '=', product_variant.id),
                                                                                        ('virtual_available', '>=', availablemeters_set.min ), ('virtual_available', '<=', availablemeters_set.max),                                                              ('location_id', '=', location_id.id)])
                            if (stock_product_variant):
                                products_with_variants.append(product.id)
            products = products.search([ ('id','in',products_with_variants) ])
        
            
        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = lazy(lambda: ProductAttribute.sudo().search([
                ('product_tmpl_ids', 'in', search_product.ids),
                ('visibility', '=', 'visible'),
            ]))
        else:
            attributes = lazy(lambda: ProductAttribute.browse(attributes_ids))

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'
            request.session['website_sale_shop_layout_mode'] = layout_mode


        products_prices = lazy(lambda: products._get_sales_prices(pricelist) or {})
        
        product_count = len(products) 
        pager = website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = products[offset:offset + ppg]

        values = {
            'search': fuzzy_search_term or search,
            'original_search': fuzzy_search_term and search,
            'order': post.get('order', ''),
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'fiberfamily_set': fiberfamily_set,
            'colorgroup_set': colorgroup_set,
            'structure_set': structure_set,
            'property_set': property_set,
            'usage_set': usage_set,
            'availablemeters_set': availablemeters_set.id if availablemeters_set else False,
            'producttype_set': producttype_set,
            'careinstructions_set': careinstructions_set,
            'certification_set': certification_set,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_product': search_product,
            'search_count': product_count,  # common for all searchbox
            'bins': lazy(lambda: TableCompute().process(products, ppg, ppr)),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            'products_prices': products_prices,
            'get_product_prices': lambda product: lazy(lambda: products_prices[product.id]),
            'float_round': tools.float_round,
        }
        if filter_by_price_enabled:
            values['min_price'] = min_price or available_min_price
            values['max_price'] = max_price or available_max_price
            values['available_min_price'] = tools.float_round(available_min_price, 2)
            values['available_max_price'] = tools.float_round(available_max_price, 2)
        if category:
            values['main_object'] = category
        values.update(self._get_additional_shop_values(values))
        return request.render("website_sale.products", values)


