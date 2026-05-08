
from odoo import api, fields, models, _


class AvailableMeters(models.Model):
    _name = 'product.available.meters'
    _description = 'Modelo para añadir propiedades de Available Meters'

    name = fields.Char(string='Name')
    min = fields.Float(string='Mínimo')
    max = fields.Float(string='Máximo')
