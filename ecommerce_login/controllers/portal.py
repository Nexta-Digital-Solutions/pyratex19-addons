# -*- coding: utf-8 -*-
"""Odoo 19: NIF opcional en la dirección de facturación de la tienda.

El módulo l10n_es de Odoo 19 hace obligatorio el NIF (vat) en la dirección de
facturación de los clientes españoles. Los clientes de la tienda son contactos
que pertenecen a una empresa (los crea el formulario de alta) y, para un
contacto, Odoo solo deja editar el NIF en la empresa: el campo sale bloqueado,
el cliente no puede rellenarlo y el checkout vuelve una y otra vez a la página
de la dirección.

Se recupera el comportamiento de Odoo 17: el NIF se puede indicar, pero no es
obligatorio. Las facturas a clientes sin NIF se emiten como en la versión anterior.
"""
from odoo.addons.l10n_es.controllers.portal import L10nESPortalAccount


class PyratexPortalAccount(L10nESPortalAccount):

    def _get_mandatory_billing_address_fields(self, country_sudo):
        field_names = super()._get_mandatory_billing_address_fields(country_sudo)
        field_names.discard('vat')
        return field_names
