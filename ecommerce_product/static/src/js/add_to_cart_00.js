odoo.define('ecommerce_product.add_to_cart_extend', function (require) {
    'use strict';
    
    const publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;
    var session = require('web.session');
       
    publicWidget.registry.websiteSaleCartLin = publicWidget.registry.websiteSaleCartLink.extend({
        _onClickAdd: function (ev) {
            ev.preventDefault();
            user_id = session.user_id;
            console.log(user_id);

            var def = () => {
                this.getCartHandlerOptions(ev);
                return this._handleAdd($(ev.currentTarget).closest('form'));
            };
            if ($('.js_add_cart_variants').children().length) {
                return this._getCombinationInfo(ev).then(() => {
                    return !$(ev.target).closest('.js_product').hasClass("css_not_available") ? def() : Promise.resolve();
                });
            }
            return def();
        },


    });
});