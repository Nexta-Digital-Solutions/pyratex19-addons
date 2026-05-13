odoo.define('ecommerce_product.add_to_cart', function (require) {
    "use strict";
    const rpc = require('web.rpc');
    const ajax = require('web.ajax');
    var wSaleUtils = require('website_sale.utils');
    const session = require('web.session');

    const getSelectedProductIds = require('ecommerce_product.add_to_the_pack').getSelectedProductIds;

        async function getIdFromProductName(ProductName) {
        let result;

        await rpc.query({
            model: 'product.product',
            method: 'getOpenPackProductId',
			args: [[ []], ProductName ]
        }).then(function (data) {
            console.log('Data', data);
            result = data});
        return result;
        };

        async function getIdFromProducTemplateId(productId) {
            let result;
    
            await rpc.query({
                model: 'product.product',
                method: 'search_read',
                args: [[ ['product_tmpl_id','=', productId]], ['id', 'list_price'] ]
            }).then(function (data) {
                data[0].list_price = 0;
                result = data});
            return result;
            };


    async function setPackPrice(id, price) {
        console.log('Setting pack price. ID:', id, 'Price:', price);
        const result = await rpc.query({
            model: 'product.template',
            method: 'write',
            args: [[id], {list_price: parseFloat(price)}]
        });
        console.log('Set pack price result:', result);
        return result;
    }

    $(document).on('click', '#add_to_cart', async function () {
        const user_id = session.user_id;
        if (user_id === false){ 
            const url = "/web/login";
            window.location.href = url;
        }
        
    });
   async function checkIfProductInCart(productId) {
    let isInCart = false;

    // Obtener el carrito actual
    await rpc.query({
        route: '/shop/cart',
    }).then(function (data) {
        console.log('Current cart data:', data);

        data.order_lines.forEach(function (orderLine) {
            if (orderLine.product_id[0] === productId) {
                isInCart = true;
            }
        });
    });

    return isInCart;
}

    // Esta funcion es para el pack abierto
$(document).on('click', '#o_add_to_Cart', async function () {
    let product_ids = [];
    const user_id = session.user_id;
    
    if (user_id === false){ 
        const url = "/web/login";
        window.location.href = url;
    }

    const selectedProductIds = getSelectedProductIds();

    try {
        console.log('Starting to fetch product IDs');
        for (const record of selectedProductIds) {
            const product_id = await getIdFromProducTemplateId(record);
            product_ids.push(product_id[0]);
        }
        //console.log('Fetched Product IDs:', product_ids);

        const packPrice = window.selectedPackPrice;
        //console.log('Pack Price:', packPrice);

        const resultIdOpenPack = await getIdFromProductName('Open Pack');
        //console.log('Result ID Open Pack:', resultIdOpenPack);

        if (resultIdOpenPack.length === 0) {
            throw new Error('Customized Swatch not found');
        }

//        const isOpenPackInCart = await checkIfProductInCart(resultIdOpenPack[0].id);
//        if (isOpenPackInCart) {
//            Swal.fire({
//                icon: 'error',
//                title: 'Swatchpack',
//                text: 'You can only order one Swatch Pack for each order. If you need a larger size, please remove the previous Swatchpack from the shopping cart before adding a new pack',
//            });
//            console.error('Open Pack is already in the cart.');
//            return;
//        }

        resultIdOpenPack[0].list_price = packPrice;
        const productsOpenPack = [resultIdOpenPack[0]].concat(product_ids);
        //console.log('Products to add to cart:', productsOpenPack);

        if (await existOpenPackSaleOrder()) {
            showErrorPack();
            return;
        }
        for (const record of productsOpenPack) {
            await AddProductOpenPackToCart(record.id, 1, record.list_price, this);
            //console.log('Added product to cart:', record);
        }
        //console.log('All products added to product pack successfully.');

    } catch (error) {
        showErrorPack();
        //console.error('Ops... Error adding products to product pack:', error);
    }
});

    function showErrorPack(){
        Swal.fire({
            icon: 'error',
            title: 'Swatchpack',
            text: 'You can only order one Swatch Pack for each order. If you need a larger size, please remove the previous Swatchpack from the shopping cart before adding a new pack',
        });
    }

    async function existOpenPackSaleOrder(){
        let result = false;
        await rpc.query({ 
            route: "/shop/cart/getOpenPackCount"
        }).then(function (data) {
            result = data});
        return result;
    };
    


    async function AddProductOpenPackToCart (product_id, qty, price_unit, ev) {

        const data = await rpc.query({ 
            route: "/shop/cart/update_json",
            params: {
                product_id: product_id,
                add_qty: qty,
                price_unit: price_unit
            }
        });

        const $navButton = $('header .o_wsale_my_cart').first();
        const imgContainer = $('#products_grid')
        wSaleUtils.animateClone($navButton, imgContainer, 25, 40);
        wSaleUtils.updateCartNavBar(data);
        removeUserPack();
        
    }

    async function removeUserPack(){
        await rpc.query({
            model: 'product.template',
            method: 'removeUserOpenPack',
			args: [[ []], session.user_id ]
        })
    }
});