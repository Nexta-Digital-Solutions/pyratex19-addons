
from odoo import api, fields, models, _


class CareInstructions(models.Model):
    _name = 'care.instructions'
    _description = 'Modelo para añadir propiedades de Care Instructions'

    name = fields.Char(string='Nombre')
    image = fields.Binary(string='Imagen')