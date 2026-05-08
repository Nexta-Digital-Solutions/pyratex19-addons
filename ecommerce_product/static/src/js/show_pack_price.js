odoo.define('ecommerce_product.show_pack_price', function (require) {
    "use strict";

    const rpc = require('web.rpc');

    $(document).ready(async function() {
        const packs = await getOpenPacks();
        const firstPack = packs ? packs[0] : false;
        if (firstPack) {
            $('#select-openpack').val(firstPack.id).change();
        }
    });

    $(document).on('change', '#select-openpack', async function () {
        const selectedId = $(this).val();
        // console.log(selectedId);
        if (selectedId) {
            const packs = await getOpenPacks();
            const selectedPack = packs.find(pack => pack.id === parseInt(selectedId));
            if (selectedPack) {
                clearAllProducts();
                $('#packPrice').text(selectedPack.price + '€').css('color', 'blue').css({'font-size':'25px'});
                window.selectedPackPrice = selectedPack.price;
            } else {
                $('#packPrice').text('Pack not found');
            }
        } else {
            $('#packPrice').text('');
        }
    });

    async function getOpenPacks() {
        try {
            const result = await rpc.query({
                model: 'open.pack',
                method: 'get_results',
            });
            return result;
        } catch (error) {
            return [];
        }
    }

    function clearAllProducts() {
        $('#allProducts').empty();

    }


});


