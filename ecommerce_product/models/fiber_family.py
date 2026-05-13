
from odoo import api, fields, models, _


class FiberFamily(models.Model):
    _name = 'fiber.family'
    _description = 'Modelo para añadir tipos de fibras'

    name = fields.Char(string='Nombre')