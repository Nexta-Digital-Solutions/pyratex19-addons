from odoo import api, fields, models, _
from odoo.fields import Command
from itertools import groupby
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def create_so_website(self, product_tmp_id, price):
        return self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'date_order': self.date_order,
            'order_line': self.order_line
        })

    def _prepare_order_line_update_values(self, order_line, quantity, **kwargs):
        values = super()._prepare_order_line_update_values(order_line, quantity, **kwargs)
        if 'price_unit' in kwargs:
            values["price_unit"] = kwargs.get('price_unit')

        order_lines = order_line.order_id.order_line
        all_swatches = all(line.product_id.producttype_id and line.product_id.producttype_id.name and line.product_id.producttype_id.name == "Swatches" or
                           line.product_id.producttype_id.name == "Swatchpacks" for line in order_lines)
        # all_stock = all(line.product_id.producttype_id and line.product_id.producttype_id.name == "Swatches" or
        #                          line.product_id.producttype_id.name == "Fabrics" for line in order_lines)

        # ATENCION SOLO FALLA EN LOCAL!!!!
        if all_swatches:
            values["x_studio_type_of_order"] = "e-shop Swatches"
        else:
            values["x_studio_type_of_order"] = "e-shop Stock"
        return values

    # ------------------------------------------------------------------
    # Carrito web (Odoo 19): al quitar un pack, quitar también sus muestras
    # ------------------------------------------------------------------

    def _cart_update_order_line(self, order_line, quantity, **kwargs):
        """Al eliminar del carrito un pack cerrado o el "Open Pack", elimina también
        las líneas de muestras que lo acompañan (antes lo hacía la ruta
        /shop/cart/update_json, que ya no existe en Odoo 19).

        - Pack cerrado (OCA sale_product_pack): sus líneas hijas (pack_parent_line_id).
          OCA solo las borra al editar el pedido desde el backend, no desde la web.
        - Open Pack: las líneas de muestras (Swatches) añadidas a 0 € sin pack padre.
        """
        lines_to_remove = self.env['sale.order.line']
        if quantity <= 0 and order_line:
            lines_to_remove = self._get_pack_lines_to_remove(order_line)
        res = super()._cart_update_order_line(order_line, quantity, **kwargs)
        if lines_to_remove:
            lines_to_remove.exists().unlink()
        return res

    def _get_pack_lines_to_remove(self, order_line):
        self.ensure_one()
        SaleOrderLine = self.env['sale.order.line']
        product = order_line.product_id
        swatch_lines = self.order_line.filtered(
            lambda line: line != order_line
            and line.product_id.producttype_id.name == 'Swatches'
        )
        has_pack_hierarchy = 'pack_parent_line_id' in SaleOrderLine._fields

        if product.name == 'Open Pack':
            if has_pack_hierarchy:
                swatch_lines = swatch_lines.filtered(lambda line: not line.pack_parent_line_id)
            return swatch_lines.filtered(lambda line: not line.price_unit)

        if 'pack_ok' in product._fields and product.pack_ok:
            if has_pack_hierarchy:
                children = SaleOrderLine.search([
                    ('id', 'child_of', order_line.id),
                    ('id', '!=', order_line.id),
                ])
                if children:
                    return children
            # Packs sin líneas hijas enlazadas: comportamiento anterior
            # (quitar las muestras a 0 € del carrito).
            return swatch_lines.filtered(lambda line: not line.price_unit)

        return SaleOrderLine

    def _get_update_prices_lines(self):
        """Las líneas con precio fijado por el Open Pack (pack y muestras) no se
        recalculan cuando Odoo actualiza los precios del pedido (por ejemplo, al
        elegir la dirección o el envío en el checkout)."""
        return super()._get_update_prices_lines().filtered(lambda line: not line.pyratex_price_locked)

    def _prepare_invoice(self):
        """Diario y tipo de factura según el tipo de pedido e-shop.

        Sustituye al antiguo override completo de _create_invoices, que copiaba
        el código de Odoo y se desincronizaba en cada migración.
        """
        vals = super()._prepare_invoice()
        if self.x_studio_type_of_order:
            type_of_order = self.env['product.type'].sudo().search(
                [('type_of_order', '=', self.x_studio_type_of_order)], limit=1)
            if type_of_order and type_of_order.journal_id:
                vals.update({
                    'journal_id': type_of_order.journal_id.id,
                    'x_studio_type_of_invoice': 'e-shop',
                })
        return vals

    # MAIL #


    def _cron_delete_saleorder_lines(self, days):
        date_to_delete = fields.Date.context_today(self) - timedelta(days= days)
        saleorder_ids = self.search([ ('x_studio_type_of_order','in',['e-shop Stock','e-shop Swatches']), ('state', '=','draft'),
                                      ('order_line','!=',False ) ])
        for saleorder in saleorder_ids:
            if (saleorder.create_date.date() <= date_to_delete):
                saleorder.order_line.unlink()
        return True


class SaleOrder(models.Model):
    _inherit = 'sale.order.line'

    x_studio_type_of_order = fields.Selection(string='Type of order', related='order_id.x_studio_type_of_order')