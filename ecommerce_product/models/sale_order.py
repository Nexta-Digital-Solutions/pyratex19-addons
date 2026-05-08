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

    def _prepare_order_line_update_values(self, order_line, quantity, linked_line_id=False, **kwargs):
        values = super()._prepare_order_line_update_values(order_line, quantity, linked_line_id, **kwargs)
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

    def _get_delivery_methods(self):
        return self.env['delivery.carrier'].sudo().search([('website_published', '=', True)])

    def _create_invoices(self, grouped=False, final=False, date=None):
        """ Create invoice(s) for the given Sales Order(s).

        :param bool grouped: if True, invoices are grouped by SO id.
            If False, invoices are grouped by keys returned by :meth:`_get_invoice_grouping_keys`
        :param bool final: if True, refunds will be generated if necessary
        :param date: unused parameter
        :returns: created invoices
        :rtype: `account.move` recordset
        :raises: UserError if one of the orders has no invoiceable lines.
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            order = order.with_company(order.company_id).with_context(lang=order.partner_invoice_id.lang)

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                continue

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        Command.create(
                            order._prepare_down_payment_section_line(sequence=invoice_item_sequence)
                        ),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    Command.create(
                        line._prepare_invoice_line(sequence=invoice_item_sequence)
                    ),
                )
                invoice_item_sequence += 1

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list and self._context.get('raise_if_nothing_to_invoice', True):
            raise UserError(self._nothing_to_invoice_error_message())

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ]
            )
            for _grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        type_of_order = self.env['product.type'].search([('type_of_order','=', self.x_studio_type_of_order)], limit = 1) if self.x_studio_type_of_order else False
        if (type_of_order):
            invoice_vals_list[0].update({ 
                                         'journal_id': type_of_order.journal_id.id,
                                         'x_studio_type_of_invoice': 'e-shop'
                                        })
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view(
                'mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.sale_line_ids.order_id},
                subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'))
        return moves


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