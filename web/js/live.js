// VARIABILI GLOBALI E COSTANTI

var src, dst, proto;
var $dialog = $('<div></div>')
    .html('')
    .dialog({
      closeOnEscape: false,
      open: function(event, ui) { $(".ui-dialog-titlebar-close").hide(); },
      autoOpen: false,
      title: 'Traffic Alert',
      buttons: {
        "Ok": function() {
          var request_body = src + " " + dst + " " + proto + " " + $('#myform').serialize();
          $.post(url.concat("rest/set_route"), request_body);
          $dialog.dialog('close'); }
        }
    });

// costruisce dinamicamente le checkbox per il form presente nella dialog
var checkBoxes = createCheckBoxes();

// FUNZIONI UTILI

function createCheckBoxes() {
  var result = "";

  for(fun in functions)
  {
    funKey = functions[fun].replace(/\s+/g, '');
    result += '<input type="checkbox" id="' + funKey + '" name="function" value="' + funKey + '" /> ' + functions[fun] + "<br />";
  }

  return result;
}

// crea ogni volta che c'e' un nuovo traffico entrante la nuova stringa da mostrare nella dialog
function createDialogText() {
  dialogText = "<p> Traffic entering from " + src + " to " + dst + " (Type: " + proto +")." + " Which functions do you want to enable for this traffic? </p>";
  dialogText += '<form id="myform" action="">';
  dialogText += checkBoxes;
  dialogText += '</form>';
  return dialogText;
}

function chooseFunctions() {
  $dialog.html(createDialogText(src, dst, proto));
  $dialog.dialog('open');
}

function getFirstCommunication() {
  $.get(url.concat("rest/communications")) //scateno la rest api (GET)
    .done(function(data) {

  if (data)
  {
    src = data.split('\n')[0].split(' ')[0];
  	dst = data.split('\n')[0].split(' ')[1];  
    proto = data.split('\n')[0].split(' ')[2];	
  	chooseFunctions();
  }
  else
  {
    console.log("Requested page is empty");
  }
  }).fail(function(data) { 
      console.log("Failed sending request");
    });
}


// MAIN

// ogni secondo controllo se ci sono stati nuovi tentativi di comunicazione
setInterval(getFirstCommunication, 2000);
