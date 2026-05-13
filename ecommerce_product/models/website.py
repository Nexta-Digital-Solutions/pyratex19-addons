from odoo import api, fields, models, _
class Website(models.Model):
    _inherit = 'website'

    def _search_get_details(self, search_type, order, options):
        result = super()._search_get_details(search_type, order, options)
        for i in range(0, len(result)):
            if result[i].get('model') == 'product.template':
                del result[i]
        if search_type in ['products', 'products_only', 'all']:
            result.append(self.env['product.product']._search_get_detail(self, order, options))
        return result

