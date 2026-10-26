/**
 * Odoo 19 – ecommerce_product
 *
 * Sustituye a los antiguos:
 *   - js/add_to_cart_00.js   (publicWidget websiteSaleCartLink)
 *   - js/website_sale.js     (publicWidget websiteSaleCartLink)
 *   - js/add_to_cart.js      (click en #add_to_cart -> login)
 *   - js/variant_mixin.js    (sale.VariantMixin._onChangeCombination)
 *
 * En Odoo 19 la página de producto la gestiona la Interaction
 * `WebsiteSale` (website_sale/static/src/interactions/website_sale.js),
 * que incorpora los métodos del VariantMixin. Aquí se parchea esa clase.
 */
import { patch } from "@web/core/utils/patch";
import { redirect } from "@web/core/utils/urls";
import { session } from "@web/session";
import { user } from "@web/core/user";
import { WebsiteSale } from "@website_sale/interactions/website_sale";

// Odoo 19: uid / is_internal_user ya no están en `session` (los consume
// @web/core/user y los elimina de la sesión); se leen de `user`.
function isLoggedIn() {
    return Boolean(user.userId) && !session.is_public;
}

function isPortalUser() {
    return isLoggedIn() && !user.isInternalUser;
}

function redirectToLogin() {
    const target = `${window.location.pathname}${window.location.search}`;
    redirect(`/web/login?redirect=${encodeURIComponent(target)}`);
}

patch(WebsiteSale.prototype, {
    /**
     * Los usuarios no identificados deben iniciar sesión antes de añadir al carrito.
     */
    async onClickAdd(ev) {
        if (!isLoggedIn()) {
            redirectToLogin();
            return;
        }
        return super.onClickAdd(...arguments);
    },

    /**
     * Muestra el stock virtual de la variante seleccionada y, para usuarios
     * portal, limita la cantidad pedida a ese stock.
     * `virtual_available` lo añade product.template._get_combination_info
     * de este mismo módulo.
     */
    _onChangeCombination(ev, parent, combination) {
        super._onChangeCombination(...arguments);

        const qtyAvailableEl = parent.querySelector(".oe_qty_available");
        const virtualAvailable = Math.trunc(combination.virtual_available || 0);
        if (qtyAvailableEl) {
            qtyAvailableEl.textContent = virtualAvailable;
        }

        if (isPortalUser()) {
            const qtyInput = parent.querySelector(".quantity");
            if (qtyAvailableEl && qtyInput && virtualAvailable < parseInt(qtyInput.value || 0)) {
                qtyInput.value = virtualAvailable;
            }
            parent.querySelectorAll(".oe_message_stock").forEach((el) => {
                el.style.display = "none";
            });
        }
    },
});
