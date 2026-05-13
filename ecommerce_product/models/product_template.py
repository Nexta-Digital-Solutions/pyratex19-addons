from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    country_id = fields.Many2one('res.country', string='Made in')
    width = fields.Float(string='Width', digits = (4,2))
    description_ecommerce = fields.Text(string='Ecommerce Sales Description')
    fiberfamily_id = fields.Many2one('fiber.family', string='Fiber Family')
    property_id = fields.Many2many('properties', string='Property')
    usage_id = fields.Many2many('usage', string='Usage')
    producttype_id = fields.Many2one('product.type', string='Product Type')
    structure_id = fields.Many2one('structure', string='Structure')
    careinstructions_id = fields.Many2many('care.instructions', string='Care Instructions')
    certification_id = fields.Many2many('certification', string='Certification')
    composition_id = fields.Many2many('composition', string='Composition')

    def _get_possible_combinations(self, parent_combination=None, necessary_values=None):
        
        self.ensure_one()

        if not self.active:
            return _("The product template is archived so no combination is possible.")

        necessary_values = necessary_values or self.env['product.template.attribute.value']
        necessary_attribute_lines = necessary_values.mapped('attribute_line_id')
        attribute_lines = self.valid_product_template_attribute_line_ids.filtered(lambda ptal: ptal not in necessary_attribute_lines)

        if not attribute_lines and self._is_combination_possible(necessary_values, parent_combination):
            yield necessary_values

        product_template_attribute_values_per_line = [
            ptal.product_template_value_ids._only_active()
            for ptal in attribute_lines
        ]

        for partial_combination in self._cartesian_product(product_template_attribute_values_per_line, parent_combination):
            combination = partial_combination + necessary_values
            if self._is_combination_possible(combination, parent_combination):
                if ((self.user_has_groups('base.group_user')) or \
                    (combination.ptav_product_variant_ids.is_published and not self.user_has_groups('base.group_user'))):
                    yield combination

        return _("There are no remaining possible combination.")


    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        """Override for website, where we want to:
            - take the website pricelist if no pricelist is set
            - apply the b2b/b2c setting to the result

        This will work when adding website_id to the context, which is done
        automatically when called from routes with website=True.
        """
        self.ensure_one()

        current_website = False

        if self.env.context.get('website_id'):
            current_website = self.env['website'].get_current_website()
            if not pricelist:
                pricelist = current_website.get_current_pricelist()

        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        product = self.env['product.product'].sudo().browse(combination_info['product_id']) or self
        qty_available = product.qty_available or 0
        virtual_available = product.virtual_available or 0
        
        combination_info.update( qty_available=qty_available, virtual_available = virtual_available )
       
        """ fabrics """
        if product.producttype_id.name:
            if (product.categ_id.parent_id.name.lower() == "fabric" and 
                self.user_has_groups('base.group_portal')):
                # percentage_additional = int(self.env['ir.config_parameter'].sudo().get_param('Fabric Percentage', 1)) or 0
                try:
                    percentage_additional = int(
                        self.env['ir.config_parameter'].sudo().get_param('Fabric Percentage', 1))
                except ValueError:
                    percentage_additional = 0
                if percentage_additional != 0:
                    price = round(combination_info['price'] * (1 + percentage_additional / 100),2)
                    #list_price = round(combination_info['list_price'] * (1 + percentage_additional / 100),2)
                    if ('base_unit_price' in combination_info):
                        base_unit_price =  round(combination_info['base_unit_price'] * (1 + percentage_additional / 100),2)
                        combination_info.update( base_unit_price = base_unit_price)

                combination_info.update( price = price)
       
        #tax = (1 + product.taxes_id[0].amount / 100 ) if product.taxes_id else 1
        #price = combination_info['price'] *  tax
        #combination_info.update (price = price)    

        if self.env.context.get('website_id'):
            partner = self.env.user.partner_id
            company_id = current_website.company_id
            fpos_id = self.env['website'].sudo()._get_current_fiscal_position_id(partner)
            fiscal_position = self.env['account.fiscal.position'].sudo().browse(fpos_id)
            product_taxes = product.sudo().taxes_id.filtered(lambda x: x.company_id == company_id)
            taxes = fiscal_position.map_tax(product_taxes)

            price = self._price_with_tax_computed(
                combination_info['price'], product_taxes, taxes, company_id, pricelist, product,
                partner
            )
            if pricelist.discount_policy == 'without_discount':
                list_price = self._price_with_tax_computed(
                    combination_info['list_price'], product_taxes, taxes, company_id, pricelist,
                    product, partner
                )
            else:
                list_price = price
            price_extra = self._price_with_tax_computed(
                combination_info['price_extra'], product_taxes, taxes, company_id, pricelist,
                product, partner
            )
            has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1
            prevent_zero_price_sale = not price and current_website.prevent_zero_price_sale

            compare_list_price = self.compare_list_price
            if pricelist and pricelist.currency_id != product.currency_id:
                compare_list_price = self.currency_id._convert(self.compare_list_price, pricelist.currency_id, self.env.company,
                                                  fields.Datetime.now(), round=False)

            combination_info.update(
                base_unit_name=product.base_unit_name,
                base_unit_price=product._get_base_unit_price(list_price),
                price=price,
                list_price=list_price,
                qty_available=qty_available,
                price_extra=price_extra,
                has_discounted_price=has_discounted_price,
                prevent_zero_price_sale=prevent_zero_price_sale,
                compare_list_price=compare_list_price
            )

        return combination_info
    
    def _get_sales_prices(self, pricelist):
        pricelist.ensure_one()
        partner_sudo = self.env.user.partner_id

        # Try to fetch geoip based fpos or fallback on partner one
        fpos_id = self.env['website']._get_current_fiscal_position_id(partner_sudo)
        fiscal_position = self.env['account.fiscal.position'].sudo().browse(fpos_id)

        sales_prices = pricelist._get_products_price(self, 1.0)
        show_discount = pricelist.discount_policy == 'without_discount'
        show_strike_price = self.env.user.has_group('website_sale.group_product_price_comparison')

        base_sales_prices = self.price_compute('list_price', currency=pricelist.currency_id)

        res = {}
        for template in self:
            price_reduce = sales_prices[template.id]
            price_reduce = self.addpercentageProductPrice(template, price_reduce)

            product_taxes = template.sudo().taxes_id.filtered(lambda t: t.company_id == t.env.company)
            taxes = fiscal_position.map_tax(product_taxes)

            template_price_vals = {
                'price_reduce': price_reduce
            }
            
            base_price = None
            price_list_contains_template = pricelist.currency_id.compare_amounts(price_reduce, base_sales_prices[template.id]) != 0

            if template.compare_list_price and show_strike_price:
                # The base_price becomes the compare list price and the price_reduce becomes the price
                base_price = template.compare_list_price
                if not price_list_contains_template:
                    price_reduce = base_sales_prices[template.id]
                    template_price_vals.update(price_reduce=price_reduce)
                if template.currency_id != pricelist.currency_id:
                    base_price = template.currency_id._convert(
                        base_price,
                        pricelist.currency_id,
                        self.env.company,
                        fields.Datetime.now(),
                        round=False
                    )
            elif show_discount and price_list_contains_template:
                base_price = base_sales_prices[template.id]

            base_price = self.addpercentageProductPrice(template, base_price)
            if base_price and base_price != price_reduce:
                if not template.compare_list_price:
                    # Compare_list_price are never tax included
                    base_price = self._price_with_tax_computed(
                        base_price, product_taxes, taxes, self.env.company.id,
                        pricelist, template, partner_sudo,
                    )
                template_price_vals['base_price'] = base_price
            """  
            template_price_vals['price_reduce'] = self._price_with_tax_computed(
                template_price_vals['price_reduce'], product_taxes, taxes, self.env.company.id,
                pricelist, template, partner_sudo,
            ) 
        
            try:
                template_price_vals['price_reduce'] = template_price_vals['price_reduce'] * (1 +  product_taxes[0].amount /100 )
            except Exception as e:
                pass
            """ 
            res[template.id] = template_price_vals

        return res
    
    def addpercentageProductPrice(self, template, price):
        try:
            if template.categ_id.parent_id.name:
                if (template.categ_id.parent_id.name.lower() == "fabric" and 
                    self.user_has_groups('base.group_portal')):
                    try:
                        percentage_additional = int(
                            self.env['ir.config_parameter'].sudo().get_param('Fabric Percentage', 1))
                    except ValueError:
                        percentage_additional = 0
                    if percentage_additional > 0:
                        price_new = round(price * (1 + percentage_additional / 100),2)
                    return price_new
                return price
        except Exception:
            return price if price else 0
        
    def saveProductOpenPack(self,product_ids, user_id, pack_name_id):
        user_openpack = self.env['user.open.pack']
        record_openpack = user_openpack.sudo().search( [('user_id','=', user_id)])
        if (record_openpack):
            record_openpack.sudo().update( { 
                                            'product_template_id': [ (6,0, product_ids) ],
                                            'pack_name_id': int(pack_name_id)
                                        })
        else:
            user_openpack.sudo().create ({
                'user_id': user_id,
                'product_template_id': [ (6, 0, product_ids) ],
                'pack_name_id': int(pack_name_id)
            })
    
    def removeUserOpenPack(self, user_id):
       self.env['user.open.pack'].sudo().search( [('user_id','=', user_id)]).unlink()