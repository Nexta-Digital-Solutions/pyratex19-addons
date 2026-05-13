
from odoo import api, fields, models, _

class Usage(models.Model):
    _name = 'usage'
    _description = 'Modelo para añadir la forma de empleo'

    name = fields.Char(string='Nombre')
