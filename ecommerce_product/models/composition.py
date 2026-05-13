from odoo import api, fields, models, _


class Composition(models.Model):
    _name = 'composition'
    _description = 'Modelo para añadir propiedades de Composition'

    name = fields.Char(string='Nombre')
