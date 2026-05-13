from odoo import api, fields, models, _
from datetime import datetime

class UserOpenPack(models.Model):
    _name = 'user.open.pack'
    _description = 'Modelo para añadir los usuarios con el pack abierto'

    user_id = fields.Many2one('res.users', string='Usuario')
    product_template_id = fields.Many2many('product.template', string='Product')
    pack_name_id = fields.Many2one('open.pack', string='Pack')
    date = fields.Date(string = "Date", default=datetime.today())