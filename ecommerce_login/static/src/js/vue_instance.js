$( document ).ready(function(){
    Vue.config.devtools = true
    let divFields = new Vue({
    el: '#divFields',
    data: {
      name: '',
      lastname: '',
      email: '',
      phonenumber: '',
      address1: '',
      address2: '',
      postalcode: '',
      city: '',
      country: '',
      'invoice_name':''
    },
    });
    
   
      var checkbox = document.getElementById("flexCheckDefault");
      var billingAddressContainer = document.getElementById("billingAddressContainer");
      if (checkbox){
        checkbox.addEventListener("change", function() {
          if (this.checked) {
            billingAddressContainer.style.display = "block";
            Array.from(
              document.querySelectorAll('[id^="invoice_"]'))
              .forEach(function (x) { 
                  if (! x.hasAttribute('data-norequired')) {
                    x.setAttribute('required', true)
                  }
              }
            ); 
          } else {
            Array.from(
              document.querySelectorAll('[id^="invoice_"]'))
              .forEach(function (x) { 
                  x.removeAttribute('required')
              }
            );
            billingAddressContainer.style.display = "none";
          }
        });
      };

      let modal_save = document.getElementById('modal_save');
      if (modal_save){
        modal_save.addEventListener('click', (e) => {
          e.preventDefault();
          var el = $('#form-mlnda');
          var data = el.serializeJSON();
          var canvas = document.getElementById('signature-pad');
          var dataURL = canvas.toDataURL();
          if (canvas.toDataURL() == document.getElementById('blank').toDataURL() 
            || document.querySelector('#position').value =='') {
            appendAlert('Sign and fill your position !!!', 'danger');
            return;
          }
          $('#modal_loader').show();
          $.ajax({
              type: 'POST',
              url: '/web/signup/saveMldna',
              data: { data, 'img': dataURL},
              context: this
          }).done(function(responseText) {
                $('#modal_loader').hide();
                $('#modal_dlna_process_complete').modal('show');
          });
        })
      }

      let btn_modal_complete = document.querySelector('#btn_close_process_complete');
      if (btn_modal_complete) {
        btn_modal_complete.addEventListener('click', (e) => {
          e.preventDefault();
          $('#modal_lnda').hide();
          with (window.location){
           const url = `${protocol}//${host}/web/login`;
           window.location.href = url;
          }
        });
      }

    //firma
    function pointerDown(evt) {
      ctx.beginPath();
      ctx.moveTo(evt.offsetX, evt.offsetY);
      canvas.addEventListener("mousemove", paint, false);
    }

    function pointerUp(evt) {
        canvas.removeEventListener("mousemove", paint);
        paint(evt);
    }

    function paint(evt) {
        ctx.lineTo(evt.offsetX, evt.offsetY);
        ctx.stroke();
    }

  var canvas = document.getElementById("signature-pad");
  if (canvas){
    ctx = canvas.getContext("2d");  
    canvas.addEventListener("mousedown", pointerDown, false);
    canvas.addEventListener("mouseup", pointerUp, false); 
  }

  //alert message MDNA
  const alertPlaceholder = document.getElementById('liveAlertPlaceholder')
  const appendAlert = (message, type) => {
    const wrapper = document.createElement('div')
    wrapper.innerHTML = [
      `<div class="alert alert-${type} alert-dismissible" role="alert">`,
      `   <div>${message}</div>`,
      '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
      '</div>'
    ].join('')

    alertPlaceholder.append(wrapper)
  }


});