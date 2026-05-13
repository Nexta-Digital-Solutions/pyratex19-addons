from odoo import api, fields, models, _
from odoo.fields import Command

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    check_price = fields.Boolean(string = "Check Price", help = "To check price for 25% increment to fabrics product")
   
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            # check if there is already invoiced amount. if so, the price shouldn't change as it might have been
            # manually edited
            if line.qty_invoiced > 0 or (line.product_id.expense_policy == 'cost' and line.is_expense):
                continue
            if not line.product_uom or not line.product_id:
                line.price_unit = 0.0
            else:
                line = line.with_company(line.company_id)
                price = line._get_display_price()
                price = self.addPercentageProductFabric(line, price)
                line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
                        price,
                        line.currency_id or line.order_id.currency_id,
                        product_taxes=line.product_id.taxes_id.filtered(
                            lambda tax: tax.company_id == line.env.company
                        ),
                        fiscal_position=line.order_id.fiscal_position_id,
                    )
               
                
    def addPercentageProductFabric(self, line, price):
        percentage_additional = int(self.env['ir.config_parameter'].sudo().get_param('Fabric Percentage', 1))
        if (line.product_id.categ_id.name.lower() == "fabric" and self.user_has_groups('base.group_portal') 
            or (line.product_id.categ_id.parent_id and line.product_id.categ_id.parent_id.name.lower() == "fabric") 
            and self.user_has_groups('base.group_portal')):
                price_unit = price * (1 + percentage_additional / 100) 
                return price_unit
        return price
            