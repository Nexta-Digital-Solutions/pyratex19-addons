/**
 * Odoo 19 – ecommerce_product: "Open Pack" (pack de muestras configurable)
 *
 * Sustituye a los antiguos:
 *   - js/add_to_the_pack.js  (selección de muestras para el pack)
 *   - js/show_pack_price.js  (precio del pack seleccionado)
 *   - js/add_to_cart.js      (botón #o_add_to_Cart del pack abierto)
 *
 * Elementos del DOM que usa (views/website/products_custom.xml y
 * views/website/products_item_custom.xml):
 *   #select-openpack, #packPrice, #o_add_to_Cart, #allProducts,
 *   #o_add_to_the_pack[data-product-id]
 */
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { browser } from "@web/core/browser/browser";
import { redirect } from "@web/core/utils/urls";
import { _t } from "@web/core/l10n/translation";
import { session } from "@web/session";
import { user } from "@web/core/user";

/** Llamada ORM genérica (equivalente al antiguo rpc.query({model, method, args})). */
function callKw(model, method, args = [], kwargs = {}) {
    return rpc(`/web/dataset/call_kw/${model}/${method}`, { model, method, args, kwargs });
}

// Odoo 19: el uid ya no está en `session` (lo consume @web/core/user).
function isLoggedIn() {
    return Boolean(user.userId) && !session.is_public;
}

function redirectToLogin() {
    const target = `${window.location.pathname}${window.location.search}`;
    redirect(`/web/login?redirect=${encodeURIComponent(target)}`);
}

export class OpenPack extends Interaction {
    static selector = "#products_grid";

    dynamicContent = {
        "#o_add_to_the_pack": { "t-on-click.prevent": this.locked(this.onClickAddToPack) },
        "#allProducts": { "t-on-click": this.onClickPackArea },
        "#select-openpack": { "t-on-change": this.onChangePack },
        "#o_add_to_Cart": { "t-on-click.prevent": this.locked(this.onClickAddPackToCart, true) },
    };

    setup() {
        this.selectedProductIds = [];
        this.packs = [];
        this.userPack = null;
        this.packSelectEl = this.el.querySelector("#select-openpack");
        this.packPriceEl = this.el.querySelector("#packPrice");
        this.packContainerEl = this.el.querySelector("#allProducts");
    }

    async willStart() {
        const hasPackUi = this.packSelectEl || this.el.querySelector("#o_add_to_the_pack");
        if (!hasPackUi) {
            return;
        }
        const promises = [callKw("open.pack", "get_results").catch(() => [])];
        if (isLoggedIn()) {
            promises.push(
                callKw("user.open.pack", "search_read", [
                    [["user_id", "=", user.userId]],
                    ["product_template_id", "pack_name_id"],
                ]).catch(() => [])
            );
        }
        const [packs, userPacks] = await Promise.all(promises);
        this.packs = packs || [];
        this.userPack = (userPacks && userPacks[0]) || null;
    }

    start() {
        if (!this.packSelectEl) {
            return;
        }
        // Restaurar el pack guardado del usuario o seleccionar el primero.
        const savedPackId = this.userPack?.pack_name_id?.[0];
        if (savedPackId) {
            this.packSelectEl.value = String(savedPackId);
        } else if (this.packs.length) {
            this.packSelectEl.value = String(this.packs[0].id);
        }
        this._renderPackPrice();

        for (const templateId of this.userPack?.product_template_id || []) {
            if (Number.isInteger(templateId)) {
                this._addProduct(templateId);
            }
        }
    }

    // ------------------------------------------------------------------
    // Handlers
    // ------------------------------------------------------------------

    async onClickAddToPack(ev) {
        if (!isLoggedIn()) {
            redirectToLogin();
            return;
        }
        const productId = parseInt(ev.currentTarget.dataset.productId);
        if (!productId) {
            return;
        }
        if (this.selectedProductIds.length >= this._getMaxElements()) {
            this._notify(_t("You cannot add more products to this pack."), "warning");
            return;
        }
        this._addProduct(productId);
        await this.waitFor(this._saveUserPack());
    }

    async onClickPackArea(ev) {
        const removeBtn = ev.target.closest(".remove-from-pack");
        if (!removeBtn) {
            return;
        }
        ev.preventDefault();
        const productId = parseInt(removeBtn.dataset.productId);
        const index = this.selectedProductIds.indexOf(productId);
        if (index === -1) {
            return;
        }
        this.selectedProductIds.splice(index, 1);
        // Solo se elimina una imagen (un mismo producto puede estar varias veces).
        this.packContainerEl.querySelector(`[data-pack-product-id="${productId}"]`)?.remove();
        await this.waitFor(this._saveUserPack());
    }

    async onChangePack() {
        this.selectedProductIds = [];
        this.packContainerEl?.replaceChildren();
        this._renderPackPrice();
        if (isLoggedIn()) {
            await this.waitFor(this._saveUserPack());
        }
    }

    async onClickAddPackToCart() {
        if (!isLoggedIn()) {
            redirectToLogin();
            return;
        }
        const packId = parseInt(this.packSelectEl?.value);
        if (!packId) {
            return;
        }
        if (!this.selectedProductIds.length) {
            this._notify(_t("Add at least one product to the pack."), "warning");
            return;
        }
        let result;
        try {
            result = await this.waitFor(
                rpc("/shop/cart/open_pack/add", {
                    pack_id: packId,
                    product_template_ids: this.selectedProductIds,
                })
            );
        } catch (error) {
            this._showPackError(error?.data?.message);
            return;
        }
        if (result?.error) {
            this._showPackError(result.message);
            return;
        }
        this._updateCartIcon(result.cart_quantity);
        this.selectedProductIds = [];
        this.packContainerEl?.replaceChildren();
        this._notify(_t("The pack has been added to your cart."), "success");
    }

    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------

    _getSelectedPack() {
        const packId = parseInt(this.packSelectEl?.value);
        return this.packs.find((pack) => pack.id === packId);
    }

    _getMaxElements() {
        return this._getSelectedPack()?.elements_number || 0;
    }

    _renderPackPrice() {
        if (!this.packPriceEl) {
            return;
        }
        const pack = this._getSelectedPack();
        if (!this.packSelectEl?.value) {
            this.packPriceEl.textContent = "";
        } else if (pack) {
            this.packPriceEl.textContent = `${pack.price}€`;
            this.packPriceEl.style.color = "blue";
            this.packPriceEl.style.fontSize = "25px";
        } else {
            this.packPriceEl.textContent = _t("Pack not found");
        }
    }

    _addProduct(productId) {
        this.selectedProductIds.push(productId);
        if (!this.packContainerEl) {
            return;
        }
        const wrapper = document.createElement("div");
        wrapper.dataset.packProductId = productId;
        Object.assign(wrapper.style, {
            position: "relative",
            display: "inline-block",
            marginRight: "10px",
            width: "100px",
            height: "100px",
            overflow: "hidden",
        });

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "remove-from-pack";
        removeBtn.dataset.productId = productId;
        removeBtn.innerHTML = "&#10006;";
        Object.assign(removeBtn.style, {
            position: "absolute",
            top: "5px",
            right: "5px",
            zIndex: "1",
        });

        const img = document.createElement("img");
        img.className = "img-openpack";
        img.src = `/web/image/product.template/${productId}/image_128`;
        img.style.width = "100px";
        img.style.height = "100px";

        wrapper.append(removeBtn, img);
        this.packContainerEl.append(wrapper);
    }

    _saveUserPack() {
        const packId = this.packSelectEl?.value;
        if (!packId || !isLoggedIn()) {
            return Promise.resolve();
        }
        return callKw("product.template", "saveProductOpenPack", [
            [],
            this.selectedProductIds,
            user.userId,
            packId,
        ]);
    }

    _updateCartIcon(cartQuantity) {
        if (cartQuantity === undefined) {
            return;
        }
        browser.sessionStorage.setItem("website_sale_cart_quantity", cartQuantity);
        for (const el of document.querySelectorAll(".my_cart_quantity")) {
            if (!cartQuantity) {
                el.classList.add("d-none");
                continue;
            }
            document.querySelector("li.o_wsale_my_cart")?.classList.remove("d-none");
            el.classList.remove("d-none");
            el.classList.add("o_mycart_zoom_animation");
            this.waitForTimeout(() => {
                el.textContent = cartQuantity;
                el.classList.remove("o_mycart_zoom_animation");
            }, 300);
        }
    }

    _showPackError(message) {
        const text =
            message ||
            _t(
                "You can only order one Swatch Pack for each order. If you need a larger size, please remove the previous Swatchpack from the shopping cart before adding a new pack"
            );
        if (window.Swal) {
            window.Swal.fire({ icon: "error", title: "Swatchpack", text });
        } else {
            this._notify(text, "danger");
        }
    }

    _notify(message, type = "info") {
        this.services.notification.add(message, { type });
    }
}

registry.category("public.interactions").add("ecommerce_product.open_pack", OpenPack);
