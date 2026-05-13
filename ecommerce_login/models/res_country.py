from odoo import fields, models, _


class ResCountryWebsite(models.Model):
    _inherit = 'res.country'
    
    show_website = fields.Boolean(string = "Show Website")