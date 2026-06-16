from odoo import api, fields, models, _
from odoo.fields import Command

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    check_price = fields.Boolean(string = "Check Price", help = "To check price for 25% increment to fabrics product")

    def _reset_price_unit(self):
        self.ensure_one()

        line = self.with_company(self.company_id)
        price = line._get_display_price()
        price = self.addPercentageProductFabric(line, price)
        product_taxes = line.product_id.taxes_id._filter_taxes_by_company(line.company_id)
        price_unit = line.product_id._get_tax_included_unit_price_from_price(
            price,
            product_taxes=product_taxes,
            fiscal_position=line.order_id.fiscal_position_id,
        )
        line.update({
            'price_unit': price_unit,
            'technical_price_unit': price_unit,
        })
                
    def addPercentageProductFabric(self, line, price):
        percentage_additional = int(self.env['ir.config_parameter'].sudo().get_param('Fabric Percentage', 1))
        if (line.product_id.categ_id.name.lower() == "fabric" and self.env.user.has_group('base.group_portal')
            or (line.product_id.categ_id.parent_id and line.product_id.categ_id.parent_id.name.lower() == "fabric") 
            and self.env.user.has_group('base.group_portal')):
                price_unit = price * (1 + percentage_additional / 100) 
                return price_unit
        return price
            