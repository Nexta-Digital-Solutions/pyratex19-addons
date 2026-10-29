from odoo import api, fields, models, _, tools
import logging
from odoo.osv import expression
from collections import defaultdict, OrderedDict

_logger = logging.getLogger(__name__)



class ProductProduct(models.Model):
    _inherit = ['product.product']

    colorgroup_id = fields.Many2one('color.group', string='Color Groups', readonly=False)

    # Publicación de cada variante en la web (Odoo estándar solo publica la
    # plantilla y las variantes heredan ese valor). Este campo propio de la
    # variante decide qué variantes (colores) se ven en la tienda.
    is_published = fields.Boolean(
        string='Is Published',
        default=True,
        copy=False,
        index=True,
        help="Si está desmarcado, esta variante no se muestra en la web "
             "(círculos de color de la tienda y selector de la ficha) ni se puede añadir al carrito.",
    )


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
        # Las variantes no publicadas solo las pueden añadir los usuarios internos
        # (que las ven en la web, como en Odoo 17).
        return self.env.user.has_group('base.group_system') or (
            self.active and self.sale_ok and (self.is_published or self.env.user._is_internal()))
 
