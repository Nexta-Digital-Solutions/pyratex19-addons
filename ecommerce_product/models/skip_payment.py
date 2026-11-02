from odoo import fields, models
from odoo.http import request


class ResPartner(models.Model):
    _inherit = 'res.partner'

    skip_website_checkout_payment = fields.Boolean(
        string="Skip website checkout payment",
        help="Los pedidos web de este cliente se confirman sin pasar por el pago online.",
    )


class Website(models.Model):
    _inherit = 'website'

    checkout_skip_payment = fields.Boolean(compute='_compute_checkout_skip_payment')

    def _compute_checkout_skip_payment(self):
        for website in self:
            skip = False
            if request and request.session.uid:
                skip = request.env.user.partner_id.skip_website_checkout_payment
            website.checkout_skip_payment = skip
