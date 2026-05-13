
from odoo import api, fields, models, _


class Certification(models.Model):
    _name = 'certification'
    _description = 'Modelo para añadir propiedades de Certification'

    name = fields.Char(string='Nombre')
    image = fields.Binary(string='Imagen')