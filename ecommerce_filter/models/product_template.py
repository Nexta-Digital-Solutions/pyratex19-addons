from odoo import fields, models, api, _
from odoo.addons.http_routing.models.ir_http import slug, unslug


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _search_get_detail(self, website, order, options):
        with_image = options['displayImage']
        with_description = options['displayDescription']
        with_category = options['displayExtraLink']
        with_price = options['displayDetail']
        domains = [website.sale_product_domain()]
        category = options.get('category')
        min_price = options.get('min_price')
        max_price = options.get('max_price')
        attrib_values = options.get('attrib_values')
        fiberfamily = options.get('fiberfamily')
        # colorgroup = options.get('colorgroup')
        structure = options.get('structure')
        property = options.get('property')
        usage = options.get('usage')
        availablemeters = options.get('availablemeters')
        producttype = options.get('producttype')
        careinstructions = options.get('careinstructions')
        certification = options.get('certification')

        if category:
            domains.append([('public_categ_ids', 'child_of', unslug(category)[1])])
        if min_price:
            domains.append([('list_price', '>=', min_price)])
        if max_price:
            domains.append([('list_price', '<=', max_price)])
        if fiberfamily:
            domains.append([('fiberfamily_id', '=', int(fiberfamily))])
        # if colorgroup:
        #     domains.append([('product_variant_ids.colorgroup_id', '=', int(colorgroup))])
        if structure:
            domains.append([('structure_id', '=', int(structure))])
        if property:
            domains.append([('property_id', '=', int(property))])
        if usage:
            domains.append([('usage_id', '=', int(usage))])
        if availablemeters:
            domains.append([('id', 'in', availablemeters)])
        if producttype:
            domains.append([('producttype_id', '=', int(producttype))])
        if careinstructions:
            domains.append([('careinstructions_id', '=', int(careinstructions))])
        if certification:
            domains.append([('certification_id', '=', int(certification))])
        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domains.append([('attribute_line_ids.value_ids', 'in', ids)])
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domains.append([('attribute_line_ids.value_ids', 'in', ids)])
        search_fields = ['name', 'product_variant_ids.default_code']
        fetch_fields = ['id', 'name', 'website_url']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'product_variant_ids.default_code': {'name': 'product_variant_ids.default_code', 'type': 'text',
                                                 'match': True},
            'website_url': {'name': 'website_url', 'type': 'text', 'truncate': False},
        }
        if with_image:
            mapping['image_url'] = {'name': 'image_url', 'type': 'html'}
        if with_description:
            # Internal note is not part of the rendering.
            search_fields.append('description')
            fetch_fields.append('description')
            search_fields.append('description_sale')
            fetch_fields.append('description_sale')
            mapping['description'] = {'name': 'description_sale', 'type': 'text', 'match': True}
        if with_price:
            mapping['detail'] = {'name': 'price', 'type': 'html', 'display_currency': options['display_currency']}
            mapping['detail_strike'] = {'name': 'list_price', 'type': 'html',
                                        'display_currency': options['display_currency']}
        if with_category:
            mapping['extra_link'] = {'name': 'category', 'type': 'html'}
        return {
            'model': 'product.template',
            'base_domain': domains,
            'search_fields': search_fields,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-shopping-cart',
        }
