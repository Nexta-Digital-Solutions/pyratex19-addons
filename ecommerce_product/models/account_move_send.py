# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _is_es_facturae_applicable(self, move):
        """Factura-e solo para clientes con NIF.

        En Odoo 19, l10n_es_edi_facturae genera el XML de Factura-e en todas las
        facturas a clientes españoles cuando la empresa tiene certificado. Si el
        cliente no tiene NIF, la generación da error ("The partner needs a set tax
        identification number or VAT number").

        En los pedidos de la tienda, ese error se produce al enviar la factura
        automáticamente tras el pago y deshace todo el proceso: el pedido queda en
        presupuesto y no se crea la factura. Sin NIF no es posible emitir Factura-e,
        así que en ese caso no se ofrece.
        """
        return super()._is_es_facturae_applicable(move) and bool(move.commercial_partner_id.vat)
