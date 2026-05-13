
from odoo import api, fields, models, _


class Properties(models.Model):
    _name = 'properties'
    _description = 'Modelo para añadir propiedades'

    name = fields.Char(string='Nombre')
    image = fields.Binary(string='Imagen')
