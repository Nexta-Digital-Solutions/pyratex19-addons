
from odoo import api, fields, models, _


class Structure(models.Model):
    _name = 'structure'
    _description = 'Modelo para añadir Structure a los productos'

    name = fields.Char(string='Nombre')