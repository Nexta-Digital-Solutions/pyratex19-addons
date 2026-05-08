from odoo import api, fields, models, _


class ColorGroup(models.Model):
    _name = 'color.group'
    _description = 'Grupo es utilizado para englobar colores'

    name = fields.Char(string='Group')
    # product_attribute_valued_ids = fields.One2many(comodel_name="product.attribute.value", inverse_name="colorgroup_id", string="Colors", required=False)
    product_attribute_valued_ids = fields.One2many(comodel_name="product.attribute.value", inverse_name="colorgroup_id", string="Colors", required=False)