# -*- coding: utf-8 -*-
"""Registro de clientes de la tienda con firma del MNDA (Odoo 19).

Flujo:
1. /web/signup (sin token) muestra el formulario "Complete your profile".
2. El cliente rellena sus datos, firma el MNDA en el modal y pulsa "Next".
3. /web/signup/saveMldna crea la empresa, el contacto, la dirección de facturación
   y el usuario portal, genera el PDF del MNDA firmado en Documentos y envía al
   cliente el correo para establecer su contraseña.

Los enlaces con token (invitación / establecer contraseña) siguen usando el
formulario estándar de Odoo.
"""
import logging

from odoo import _, http
from odoo.fields import Command
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)

# Comercial que se asigna a los contactos creados desde la web
# (en la versión anterior estaba fijo a 10). Configurable con el parámetro
# del sistema "ecommerce_login.salesperson_id".
DEFAULT_SALESPERSON_ID = 10


def _to_int(value):
    try:
        return int(value or 0) or False
    except (TypeError, ValueError):
        return False


class AuthSignupHomeMnda(AuthSignupHome):

    @http.route()
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        # Enlaces con token (invitación, establecer contraseña) y envíos del
        # formulario estándar: comportamiento normal de Odoo.
        if qcontext.get('token') or request.httprequest.method == 'POST':
            return super().web_auth_signup(*args, **kw)
        if not qcontext.get('signup_enabled'):
            return super().web_auth_signup(*args, **kw)
        return request.render('ecommerce_login.complete_your_profile')

    @http.route('/web/complete_profile', type='http', auth='public', website=True, methods=['GET', 'POST'], sitemap=False)
    def complete_profile(self, **post):
        return request.render('ecommerce_login.complete_your_profile')

    @http.route('/web/signup/saveMldna', type='http', auth='public', website=True, methods=['POST'], sitemap=False)
    def web_saveDLNA(self, **post):
        """Recibe el formulario (data[campo]=valor) y la firma (img=dataURL)."""
        data = {key[5:-1]: value for key, value in post.items() if key.startswith('data[') and key.endswith(']')}
        signature = post.get('img')
        if not data.get('email') or not data.get('name'):
            return request.make_json_response({'error': _("Missing required data.")}, status=400)
        try:
            company = self.createCompanyDLNA(data)
            partner = self.createContactDLNA(data, signature, company)
            self.createInvoiceDLNA(data, company, partner)
            user = self.createUserDLNA(data, partner)
        except Exception:
            _logger.exception("MNDA signup: error creating the customer %s", data.get('email'))
            request.env.cr.rollback()
            return request.make_json_response({'error': _("Could not create your account.")}, status=500)

        try:
            document = partner.createDocumentMDNA(partner, data, signature)
            if document and 'x_studio_mnda_signed' in partner._fields:
                partner.sudo().x_studio_mnda_signed = 'Yes'
        except Exception:
            # El cliente queda registrado aunque falle la generación del PDF.
            _logger.exception("MNDA signup: error generating the MNDA for %s", data.get('email'))

        try:
            # Correo para que el cliente establezca su contraseña
            user.sudo().action_reset_password()
        except Exception:
            _logger.exception("MNDA signup: error sending the invitation to %s", data.get('email'))

        return request.make_json_response({'success': True})

    # ------------------------------------------------------------------
    # Creación de registros
    # ------------------------------------------------------------------

    def createUserDLNA(self, data, partner):
        email = (data.get('email') or '').strip()
        Users = request.env['res.users'].sudo()
        user = Users.with_context(active_test=False).search([('login', '=', email)], limit=1)
        if user:
            return user
        user_values = {
            'name': partner.name,
            'login': email,
            'email': email,
            'partner_id': partner.id,
            'group_ids': [Command.set([request.env.ref('base.group_portal').id])],
            'phone': data.get('phone'),
            'function': data.get('position'),
        }
        # no_reset_password: la invitación se envía una sola vez desde web_saveDLNA
        return Users.with_context(no_reset_password=True).create(user_values)

    def createCompanyDLNA(self, data):
        name = (data.get('company') or '').strip() or ' '.join(
            filter(None, [data.get('name'), data.get('lastname')]))
        Partner = request.env['res.partner'].sudo()
        company = Partner.search([('name', '=', name), ('is_company', '=', True)], limit=1)
        if not company:
            company = Partner.create({
                'company_type': 'company',
                'name': name,
                'street': data.get('address1'),
                'street2': data.get('address2'),
                'zip': data.get('postalcode'),
                'city': data.get('city'),
                'country_id': _to_int(data.get('country')),
                'phone': data.get('phone'),
                'comment': data.get('additional_instructions'),
            })
        return company

    def createContactDLNA(self, data, signature, company):
        name = ' '.join(filter(None, [data.get('name'), data.get('lastname')]))
        email = (data.get('email') or '').strip()
        Partner = request.env['res.partner'].sudo()
        partner = Partner.search([('email', '=', email)], limit=1)
        if partner:
            return partner

        values = {
            'parent_id': company.id,
            'company_type': 'person',
            'type': 'contact',
            'street': company.street,
            'street2': company.street2,
            'city': company.city,
            'zip': company.zip,
            'country_id': company.country_id.id,
            'name': name,
            'email': email,
            'phone': data.get('phone'),
            'function': data.get('position'),
        }
        profession = data.get('profession')
        if profession and profession in dict(Partner._fields['profession'].selection):
            values['profession'] = profession
        about_us = data.get('about_us')
        if about_us and about_us in dict(Partner._fields['about_us'].selection):
            values['about_us'] = about_us
        if about_us == 'other' and data.get('other_reason'):
            values['comment'] = _("How did you hear about us: %s", data.get('other_reason'))

        salesperson_id = _to_int(request.env['ir.config_parameter'].sudo().get_param(
            'ecommerce_login.salesperson_id', DEFAULT_SALESPERSON_ID))
        salesperson = request.env['res.users'].sudo().browse(salesperson_id).exists() if salesperson_id else False
        if salesperson:
            values['user_id'] = salesperson.id

        partner = Partner.create(values)
        fiscal_position = request.env['account.fiscal.position'].sudo().search(
            [('name', '=', 'EU privado')], limit=1)
        if fiscal_position:
            partner.property_account_position_id = fiscal_position
        return partner

    def createInvoiceDLNA(self, data, company, partner):
        if not data.get('invoice_name'):
            return request.env['res.partner']
        name = ' '.join(filter(None, [data.get('invoice_name'), data.get('invoice_lastname')]))
        Partner = request.env['res.partner'].sudo()
        invoice_address = Partner.search([
            ('parent_id', '=', company.id),
            ('type', '=', 'invoice'),
            ('name', '=', name),
        ], limit=1)
        if not invoice_address:
            invoice_address = Partner.create({
                'name': name,
                'parent_id': company.id,
                'company_type': 'person',
                'type': 'invoice',
                'phone': data.get('invoice_phone'),
                'street': data.get('invoice_address1'),
                'street2': data.get('invoice_address2'),
                'city': data.get('invoice_city'),
                'zip': data.get('invoice_postalcode'),
                'country_id': _to_int(data.get('invoice_country')),
                'comment': data.get('invoice_additional'),
            })
        return invoice_address
