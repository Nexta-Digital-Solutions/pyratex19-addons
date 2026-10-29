/**
 * Odoo 19 – ecommerce_login: formulario "Complete your profile" + firma del MNDA
 *
 * Sustituye a js/vue_instance.js, que dependía de Vue 2 (vue@2.7.14.js),
 * jQuery y jquery.serializejson. Ya no hace falta cargar esas librerías:
 *   - Las interpolaciones {{ campo }} de las plantillas se rellenan aquí con
 *     el valor del input que tiene v-model="campo" (o name="campo").
 *   - El envío usa los mismos nombres de parámetro que antes
 *     (data[campo]=valor & img=<dataURL>), así que /web/signup/saveMldna
 *     no necesita cambios.
 */
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { redirect } from "@web/core/utils/urls";
import { _t } from "@web/core/l10n/translation";

const BINDING_RE = /\{\{\s*([\w]+)\s*\}\}/g;

export class CompleteProfileMnda extends Interaction {
    static selector = "#form-mlnda";

    dynamicContent = {
        _root: { "t-on-submit.prevent": this.onSubmitProfile },
        "#divFields input, #divFields select, #divFields textarea": {
            "t-on-input.noUpdate": this.renderBindings,
            "t-on-change.noUpdate": this.renderBindings,
        },
        "#flexCheckDefault": { "t-on-change": this.onToggleBillingAddress },
        "#about_us_select": { "t-on-change": this.onChangeAboutUs },
        "#country": { "t-on-change": this.onChangeCountry },
        "#modal_save": { "t-on-click.prevent": this.locked(this.onClickSaveMnda) },
        "#btn_close_process_complete": { "t-on-click.prevent": this.onClickCloseComplete },
        "#signature-pad": {
            "t-on-pointerdown.noUpdate": this.onSignatureStart,
            "t-on-pointermove.noUpdate": this.onSignatureMove,
            "t-on-pointerup.noUpdate": this.onSignatureEnd,
            "t-on-pointerleave.noUpdate": this.onSignatureEnd,
        },
    };

    setup() {
        this.bindings = [];
        this.isDrawing = false;
        this.canvas = this.el.querySelector("#signature-pad");
        this.ctx = this.canvas?.getContext("2d");
        if (this.canvas) {
            // Necesario para poder firmar con el dedo en móvil/tablet.
            this.canvas.style.touchAction = "none";
        }
    }

    start() {
        this._collectBindings();
        this.renderBindings();
    }

    // ------------------------------------------------------------------
    // Interpolaciones {{ campo }} (antes Vue)
    // ------------------------------------------------------------------

    _collectBindings() {
        const root = this.el.querySelector("#divFields") || this.el;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let node;
        while ((node = walker.nextNode())) {
            if (node.nodeValue.includes("{{")) {
                this.bindings.push({ node, template: node.nodeValue });
            }
        }
    }

    _getFieldValue(fieldName) {
        const field =
            this.el.querySelector(`[v-model="${fieldName}"]`) ||
            this.el.querySelector(`[name="${fieldName}"]`) ||
            this.el.querySelector(`#${CSS.escape(fieldName)}`);
        return field?.value ?? "";
    }

    renderBindings() {
        for (const { node, template } of this.bindings) {
            node.nodeValue = template.replace(BINDING_RE, (_match, fieldName) =>
                this._getFieldValue(fieldName)
            );
        }
    }

    // ------------------------------------------------------------------
    // Formulario
    // ------------------------------------------------------------------

    onSubmitProfile() {
        // Equivale al antiguo action="javascript:showModal()".
        this._getModal("#modal_lnda")?.show();
    }

    onToggleBillingAddress(ev) {
        const checked = ev.currentTarget.checked;
        const container = this.el.querySelector("#billingAddressContainer");
        if (container) {
            container.style.display = checked ? "block" : "none";
        }
        this.el.querySelectorAll('[id^="invoice_"]').forEach((input) => {
            if (checked && !input.hasAttribute("data-norequired")) {
                input.setAttribute("required", "required");
            } else {
                input.removeAttribute("required");
            }
        });
    }

    onChangeCountry(ev) {
        // La dirección de facturación usa por defecto el mismo país
        const invoiceCountry = this.el.querySelector("#invoice_country");
        if (invoiceCountry) {
            invoiceCountry.value = ev.currentTarget.value;
        }
    }

    onChangeAboutUs(ev) {
        const otherReason = this.el.querySelector("#other_reason");
        if (otherReason) {
            otherReason.style.display = ev.currentTarget.value === "other" ? "block" : "none";
        }
    }

    async onClickSaveMnda() {
        const position = this.el.querySelector("#position");
        const blank = this.el.querySelector("#blank");
        if (!this.canvas) {
            return;
        }
        const signature = this.canvas.toDataURL();
        if ((blank && signature === blank.toDataURL()) || !position?.value) {
            this._appendAlert(_t("Sign and fill your position !!!"), "danger");
            return;
        }

        const body = new URLSearchParams();
        for (const [name, value] of new FormData(this.el)) {
            if (typeof value === "string") {
                body.append(`data[${name}]`, value);
            }
        }
        body.append("img", signature);
        // Odoo 19: la ruta valida el token CSRF
        const csrfInput = this.el.querySelector('input[name="csrf_token"]');
        if (csrfInput) {
            body.append("csrf_token", csrfInput.value);
        }

        const loader = this._getModal("#modal_loader");
        loader?.show();
        try {
            const response = await this.waitFor(
                fetch("/web/signup/saveMldna", {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
                    body,
                })
            );
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            this._getModal("#modal_lnda")?.hide();
            this._getModal("#modal_dlna_process_complete")?.show();
        } catch {
            this._appendAlert(
                _t("Something went wrong while saving the agreement. Please try again."),
                "danger"
            );
        } finally {
            loader?.hide();
        }
    }

    onClickCloseComplete() {
        this._getModal("#modal_lnda")?.hide();
        redirect("/web/login");
    }

    // ------------------------------------------------------------------
    // Firma
    // ------------------------------------------------------------------

    onSignatureStart(ev) {
        if (!this.ctx) {
            return;
        }
        this.isDrawing = true;
        this.canvas.setPointerCapture?.(ev.pointerId);
        this.ctx.beginPath();
        this.ctx.moveTo(ev.offsetX, ev.offsetY);
    }

    onSignatureMove(ev) {
        if (!this.isDrawing) {
            return;
        }
        this.ctx.lineTo(ev.offsetX, ev.offsetY);
        this.ctx.stroke();
    }

    onSignatureEnd(ev) {
        if (!this.isDrawing) {
            return;
        }
        this.onSignatureMove(ev);
        this.isDrawing = false;
    }

    // ------------------------------------------------------------------
    // Utilidades
    // ------------------------------------------------------------------

    _getModal(selector) {
        const el = this.el.querySelector(selector) || document.querySelector(selector);
        return el ? window.Modal.getOrCreateInstance(el) : null;
    }

    _appendAlert(message, type) {
        const placeholder = this.el.querySelector("#liveAlertPlaceholder");
        if (!placeholder) {
            return;
        }
        const alert = document.createElement("div");
        alert.className = `alert alert-${type} alert-dismissible`;
        alert.setAttribute("role", "alert");
        const text = document.createElement("div");
        text.textContent = message;
        const close = document.createElement("button");
        close.type = "button";
        close.className = "btn-close";
        close.dataset.bsDismiss = "alert";
        close.setAttribute("aria-label", _t("Close"));
        alert.append(text, close);
        placeholder.append(alert);
    }
}

registry
    .category("public.interactions")
    .add("ecommerce_login.complete_profile_mnda", CompleteProfileMnda);
