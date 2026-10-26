from odoo import models

# Filtros de la tienda que se resuelven con un campo directo de product.template
SIMPLE_FILTER_FIELDS = {
    'fiberfamily': 'fiberfamily_id',
    'structure': 'structure_id',
    'property': 'property_id',
    'usage': 'usage_id',
    'producttype': 'producttype_id',
    'careinstructions': 'careinstructions_id',
    'certification': 'certification_id',
}

# Almacén en el que se comprueban los metros disponibles
AVAILABLE_METERS_LOCATION = 'Spain/External Warehouse'


def _to_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _search_get_detail(self, website, order, options):
        """Odoo 19: se parte del dominio estándar (categoría, precio, etiquetas,
        atributos...) y se le añaden los filtros propios de la tienda."""
        res = super()._search_get_detail(website, order, options)
        domains = res['base_domain']

        for option, field_name in SIMPLE_FILTER_FIELDS.items():
            value = _to_int(options.get(option))
            if value:
                domains.append([(field_name, '=', value)])

        colorgroup = _to_int(options.get('colorgroup'))
        if colorgroup:
            domains.append([(
                'product_variant_ids.product_template_attribute_value_ids'
                '.product_attribute_value_id.colorgroup_id', '=', colorgroup,
            )])

        meters_id = _to_int(options.get('availablemeters'))
        if meters_id:
            domains.append([('id', 'in', self._get_templates_with_available_meters(meters_id))])

        return res

    def _get_templates_with_available_meters(self, meters_id):
        meters = self.env['product.available.meters'].sudo().browse(meters_id).exists()
        if not meters:
            return []
        Product = self.env['product.product'].sudo()
        location = self.env['stock.location'].sudo().search(
            [('complete_name', '=', AVAILABLE_METERS_LOCATION)], limit=1
        )
        if location:
            Product = Product.with_context(location=location.id)
        variants = Product.search([
            ('virtual_available', '>=', meters.min),
            ('virtual_available', '<=', meters.max),
        ])
        return variants.product_tmpl_id.ids
