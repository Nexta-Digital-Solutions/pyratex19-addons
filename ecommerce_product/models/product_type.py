
from odoo import api, fields, models, _


class ProductType(models.Model):
    _name = 'product.type'
    _description = 'Modelo para añadir tres tipos de productos'

    TYPES = [
        ('Swatches', 'Swatches'),
        ('Stock', 'Stock'),
        ('Stock Reservation', 'Stock Reservation'),
        ('SMS', 'SMS'),
        ('Production', 'Production'),
        ('Production Studio Fabric', 'Production Studio Fabric'),
        ('Developments', 'Developments'),
        ('Other revenue', 'Other Revenue'),
        ('Lab Dips', 'Lab Dips'),
        ('Consultancy & Commissions', 'Consultancy & Commissions'),
        ('Recovo', 'Recovo'),
        ('e-shop Swatches', 'e-shop Swatches'),
        ('e-shop Stock', 'e-shop Stock')
    ]

    name = fields.Char(string='Nombre')
    type_of_order = fields.Selection (TYPES, string = "Type_of_order", default=TYPES[0][0])
    journal_id = fields.Many2one('account.journal', string = "Journal", required = True)