// VARIABILI GLOBALI E COSTANTI

var details = {};
var sorgente, destinazione, protocollo;
var $dialog = $('<div></div>')
    .html('')
    .dialog({
      closeOnEscape: false,
      open: function(event, ui) { $(".ui-dialog-titlebar-close").hide(); },
      autoOpen: false,
      title: 'Change Functions',
      buttons: {
        "Ok": function() {
          var request_body = sorgente + " " + destinazione + " " + protocollo + " " + $('#myform').serialize();
          $.post(url.concat("rest/set_route"), request_body);
          $dialog.dialog('close');
          getRoutes(); },
        "Cancel": function() {$(this).dialog("close");}
      }
    });


// FUNZIONI UTILI

function formatActivated(activated) {
  var result = "";

  while(activated.indexOf(',') >= 0)
  {
    temp = activated.substring(0, activated.indexOf(','));
    for(fun in functions)
    {
      funKey = functions[fun].replace(/\s+/g, '');
      if(temp.search(funKey) >= 0)
      {
        result += functions[fun] + ", ";
        break;
      }
    }
    activated = activated.substring(activated.indexOf(',') + 1);
  }
  for(fun in functions)
    {
      funKey = functions[fun].replace(/\s+/g, '');
      if(activated.search(funKey) >= 0)
      {
        result += functions[fun];
        break;
      }
    }
    return result;
}

function createCheckBoxes(activated) {
  var result = "";

  for(fun in functions)
  {
    funKey = functions[fun].replace(/\s+/g, '');
    if(activated.search(functions[fun]) >= 0)
    {
      result += '<input type="checkbox" id="' + funKey + '" name="function" value="' + funKey + '" checked="checked"/> ' + functions[fun] + "<br />";
    }
    else
    {
      result += '<input type="checkbox" id="' + funKey + '" name="function" value="' + funKey + '" /> ' + functions[fun] + "<br />";
    }
  }

  return result;
}

function route(src, dst, proto, activated) {
    this.src = src;
    this.dst = dst;
    this.proto = proto;
    this.activated = activated;
}

function createDialogText(src, dst, proto, activated) {
  dialogText = "<p> Route from " + src + " to " + dst + " (Type: " + proto +")." + " Do you want to add or remove enabled functions? </p>";
  dialogText += '<form id="myform" action="">';
  dialogText += createCheckBoxes(activated);
  dialogText += '</form>';
  return dialogText;
}

function addEntry(entry)
{  
  var routesTableBody = document.getElementById('routes');

  var src = entry.substring(0, entry.indexOf(' '));
  entry = entry.substring(entry.indexOf(' ') + 1);
  var dst = entry.substring(0, entry.indexOf(' '));
  entry = entry.substring(entry.indexOf(' ') + 1);
  var proto = entry.substring(0, entry.indexOf(' '));
  entry = entry.substring(entry.indexOf(' ') + 1);
  var activated = formatActivated(entry);

  var tr = document.createElement('TR');

  td = document.createElement('TD');
  td.appendChild(document.createTextNode(src));
  tr.appendChild(td);

  td = document.createElement('TD');
  td.appendChild(document.createTextNode(dst));
  tr.appendChild(td);

  td = document.createElement('TD');
  td.appendChild(document.createTextNode(proto));
  tr.appendChild(td);

  td = document.createElement('TD');
  td.appendChild(document.createTextNode(activated));
  tr.appendChild(td);

  td = document.createElement('TD');
  var btn = document.createElement("BUTTON");
  btn.setAttribute("id", src + dst + proto);

  btn.onclick = function(e) {
    var detail = details[e.target.id];
    $dialog.html(createDialogText(detail.src, detail.dst, detail.proto, detail.activated));
    sorgente = detail.src;
    destinazione = detail.dst;
    protocollo = detail.proto;
    $dialog.dialog('open');
  };

  var t = document.createTextNode("Modify");
  btn.appendChild(t); 
  td.appendChild(btn);
  tr.appendChild(td);

  routesTableBody.appendChild(tr);

  var temp = new route(src, dst, proto, activated);
  details[btn.getAttribute('id')] = temp;
}

function getRoutes() {

  var routesTableBody = document.getElementById('routes');

  while (routesTableBody.firstChild) {
            routesTableBody.removeChild(routesTableBody.firstChild);
    }

  $.get(url.concat("rest/routes")) //scateno la rest api (GET)
    .done(function(data) {

  if (data)
  {
    var routes = data.split('\n');
    for(x in routes)
    {
      if(routes[x])
      {
        addEntry(routes[x]);
      }
    }
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

$( document ).ready(function() {
  getRoutes();
});