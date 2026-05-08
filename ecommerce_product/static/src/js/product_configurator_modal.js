/** @odoo-module */

import { OptionalProductsModal } from "@sale_product_configurator/js/product_configurator_modal";
import { patch } from "@web/core/utils/patch";
const session = require('web.session');

patch(OptionalProductsModal.prototype,'product_configurator_portal',{
    _onCancelButtonClick: function () {
        this.trigger('back');
        if (session.user_has_group('base.group_portal').then( has_group =>  {
            if(has_group) {
                  window.location.href = "/shop";
            }
            this.close();
        }));
        
    }
})