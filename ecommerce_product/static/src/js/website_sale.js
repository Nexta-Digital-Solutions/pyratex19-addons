odoo.define('ecommerce_product.websitesale_cart', function (require) {
    'use strict';

var publicWidget = require('web.public.widget');


publicWidget.registry.websiteSaleCartLinkCustom =  publicWidget.registry.websiteSaleCartLink.extend({

    _onClickAdd: function (ev) {
        ev.preventDefault();
        if (this.session == undefined) {
            window.location.href = "/web/login"
        }

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

