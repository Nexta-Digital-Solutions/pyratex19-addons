# -*- coding: utf-8 -*-
"""Filtros propios de la tienda (Odoo 19).

En lugar de reescribir entera la ruta /shop (la versión anterior era una copia
del controlador de Odoo 16 y no funcionaba en 19), se usan los hooks
que ofrece website_sale:

- _get_search_options: pasa los filtros a product.template._search_get_detail,
  que es donde se construye el dominio de búsqueda.
- _shop_get_query_url_kwargs: mantiene los filtros en los enlaces (keep()).
- _get_additional_shop_values: expone <filtro>_set a las plantillas para
  marcar la opción seleccionada en cada <select>.
"""
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

CUSTOM_SHOP_FILTERS = (
    'fiberfamily',
    'colorgroup',
    'structure',
    'property',
    'usage',
    'availablemeters',
    'producttype',
    'careinstructions',
    'certification',
)


def get_custom_filter_values(params):
    """Devuelve {filtro: id o False} a partir de los parámetros de la URL."""
    values = {}
    for key in CUSTOM_SHOP_FILTERS:
        try:
            values[key] = int(params.get(key) or 0) or False
        except (TypeError, ValueError):
            values[key] = False
    return values


class WebsiteSaleCustomFilters(WebsiteSale):

    def _get_search_options(self, category=None, attribute_value_dict=None, tags=None,
                            min_price=0.0, max_price=0.0, conversion_rate=1, **post):
        options = super()._get_search_options(
            category=category,
            attribute_value_dict=attribute_value_dict,
            tags=tags,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post,
        )
        options.update(get_custom_filter_values(post))
        return options

    def _shop_get_query_url_kwargs(self, search, min_price, max_price, order=None, tags=None,
                                   **kwargs):
        res = super()._shop_get_query_url_kwargs(
            search, min_price, max_price, order=order, tags=tags, **kwargs
        )
        res.update({key: value for key, value in get_custom_filter_values(kwargs).items() if value})
        return res

    def _get_additional_shop_values(self, values, **kwargs):
        res = super()._get_additional_shop_values(values, **kwargs)
        res.update({
            f'{key}_set': value
            for key, value in get_custom_filter_values(request.params).items()
        })
        return res
