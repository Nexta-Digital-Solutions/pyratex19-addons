from odoo import api, fields, models, _, tools
import logging
from odoo.osv import expression
from collections import defaultdict, OrderedDict

_logger = logging.getLogger(__name__)



class ProductProduct(models.Model):
    _inherit = ['product.product', "website.seo.metadata",
                'website.published.multi.mixin',
                'website.searchable.mixin',
                'rating.mixin']

    _name = 'product.product'

    colorgroup_id = fields.Many2one('color.group', string='Color Groups', readonly=False)


    @api.onchange('colorgroup_id')
    def _onchange_colorgroup_id(self):
        for product in self:
            color = product.product_template_attribute_value_ids.filtered(
                lambda template: template.display_type == 'color')
            if color:
                color.product_attribute_value_id.update({'colorgroup_id': product.colorgroup_id.id})

    def getOpenPackProductId (self, productName):
        product_id = self.env['product.product'].sudo().search([ ('name','=',productName)], limit = 1)
        dict = {
            'id': product_id.id,
            'list_price': product_id.list_price
        }
        return [ dict ] if product_id else False
    
    def _is_add_to_cart_allowed(self):
        self.ensure_one()
        return self.user_has_groups('base.group_system') or (self.active and self.sale_ok)
 
