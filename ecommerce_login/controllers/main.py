import logging
import werkzeug
from werkzeug.urls import url_encode

from odoo import http, tools, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.home import ensure_db, Home, SIGN_UP_REQUEST_PARAMS, LOGIN_SUCCESSFUL_PARAMS
from odoo.addons.base_setup.controllers.main import BaseSetup
from odoo.exceptions import UserError
from odoo.http import request
import json

_logger = logging.getLogger(__name__)

LOGIN_SUCCESSFUL_PARAMS.add('account_created')


class AuthSignupHome(Home):
    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext:
        #and request.httprequest.method == 'POST':
            try:
                #self.do_signup(qcontext)
                if qcontext.get('token'):
                    User = request.env['res.users']
                    user_sudo = User.sudo().search(
                        User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                    )
                    template = request.env.ref('auth_signup.mail_template_user_signup_account_created',
                                               raise_if_not_found=False)
                    if user_sudo and template:
                        template.sudo().send_mail(user_sudo.id, force_send=True)
                return request.render('ecommerce_login.complete_your_profile')  # renderiza la vista
                # return request.redirect('/web/complete_profile')
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")

        elif 'signup_email' in qcontext:
            user = request.env['res.users'].sudo().search(
                [('email', '=', qcontext.get('signup_email')), ('state', '!=', 'new')], limit=1)
            if user:
                return request.redirect('/web/login?%s' % url_encode({'login': user.login, 'redirect': '/web'}))

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    # Método para recibir los datos del formulario
    @http.route('/web/complete_profile', type='http', auth='public', website=True, methods=['POST'])
    def complete_profile(self, **post):
        return request.render('ecommerce_login.complete_your_profile')
    
    @http.route('/web/signup/saveMldna', type='http', auth='public', website=True, sitemap=False, csrf = False)
    def web_saveDLNA(self, **post):
        params = post
        signature = params.get('img')
        company_id = self.createCompanyDLNA(params)
        partner_id = self.createContactDLNA(params, signature, company_id)
        invoice_id = self.createInvoiceDLNA(params,company_id, partner_id)
        if (partner_id): 
            try:       
                user_id = self.createUserDLNA(params, partner_id)
                user_id.action_reset_password()
            except:
                pass
            doc_id = partner_id.createDocumentMDNA(partner_id, params, signature)
            if (doc_id):
                partner_id.sudo().update ({
                    'x_studio_mnda_signed': 'Yes'
                })
        else:
            return request.redirect('/web/login')

    def createUserDLNA(self, data, parent_id):
        name = ' '.join([data.get('data[name]'), data.get('data[lastname]')])
        email = data.get('data[email]')
        user_data = {
            'name': name,
            'login': email,
            'sel_groups_1_9_10': 9,
            'partner_id': parent_id.id,
            'mobile': data.get('data[phone]'),
            'street': data.get('data[address1]'),
            'street2': data.get('data[address2]'),
            'zip': data.get('data[postalcode]'),
            'city': data.get('data[city]'),
            'state': False,
            'country_id':  int(data.get('data[country]')),
            'function': data.get('data[position]')     
        }
        
        user = request.env['res.users'].sudo().search([ ('login', '=', email) ])
        if (not user):
            user = request.env['res.users'].sudo().create( user_data )
        return user
    
    def createCompanyDLNA(self, data):
        company = data.get('data[company]')
        company_id = request.env['res.partner'].sudo().search([ ('name', '=', company) ], limit = 1)
        contact = {
            'company_type': 'company',
            'name': company,
            'street': data.get('data[address1]'),
            'street2': data.get('data[address2]'),
            'zip': data.get('data[postalcode]'),
            'country_id':  int(data.get('data[country]')),
            'city': data.get('data[city]'),
            'comment': data.get('data[additional_instructions]')
        } 
        if (not company_id):
            company_id = request.env['res.partner'].sudo().create( contact )
        return company_id     
     
    def createContactDLNA(self, data, signature, company_id):
        name = ' '.join([data.get('data[name]'), data.get('data[lastname]')])
        email = data.get('data[email]')
        fiscal_position_id = request.env['account.fiscal.position'].sudo().search([('name','=', 'EU privado')], limit = 1)
        contact = {
            'parent_id': company_id.id,
            'company_type': 'person',
            'type': 'contact',
            'street': company_id.street,
            'street2': company_id.street2,
            'city': company_id.city,
            'zip': company_id.zip,
            'country_id': company_id.country_id.id,
            'name': name,
            'email': email,
            'profession': data.get('data[profession]'),
            'about_us': data.get('data[about_us]'),
            'user_id': 10
        }
        
        partner_id = request.env['res.partner'].sudo().search([ ('email', '=', email) ], limit = 1)
        if (not partner_id):
            partner_id = request.env['res.partner'].sudo().create( contact )
            partner_id.update ({ 'property_account_position_id': fiscal_position_id.id if fiscal_position_id else False })
        return partner_id
        
    def createInvoiceDLNA(self, data, company_id, partner_id):
        invoice_name =  data.get('data[invoice_name]')
        if (not invoice_name):
            return
        
        name = ' '.join([data.get('data[invoice_name]'), data.get('data[invoice_lastname]')])
        invoice_address = {
            'name': name,
            'parent_id': company_id.id,
            'company_type': 'person',
            'type': 'invoice',
            'street': data.get('data[invoice_address1]'),
            'street2': data.get('data[invoice_address2]'),
            'city': data.get('data[invoice_city]'),
            'zip': data.get('data[invoice_postalcode]'),
            'country_id':  int(data.get('data[invoice_country]')),
            'comment': data.get('data[invoice_additional]')
        }
        partner_id = request.env['res.partner'].sudo().search([ ('name', 'ilike', name) ], limit = 1)
        if (not partner_id):
           partner_id = request.env['res.partner'].sudo().create( invoice_address )
        return partner_id