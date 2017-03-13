# Copyright (C) 2014 SDN Hub
#
# Licensed under the GNU GENERAL PUBLIC LICENSE, Version 3.
# You may not use this file except in compliance with this License.
# You may obtain a copy of the License at
#
#    http://www.gnu.org/licenses/gpl-3.0.txt
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.

import json
from webob import Response
import os
import mimetypes

from ryu.base import app_manager
from ryu.app.wsgi import ControllerBase, WSGIApplication


# REST API
#
############# Configure tap
#
# get root
# GET /
#
# get file
# GET /web/{file}
#

class WebController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(WebController, self).__init__(req, link, data, **config)
        # L'istruzione sottostante semplicemente concatena le stringhe passate come parametro a os.path.join e assegna il risultato all'attributo directory di self
        # os.path.dirname(os.path.abspath(__file__)) restituisce la cartella dove questo file e' contenuto
        # Il risultato e' percorso_cartella_di_questo_file/web
        self.directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')

    def make_response(self, filename):

    	# Trovo il tipo di file e l'encoding usato nella pagina web
        filetype, encoding = mimetypes.guess_type(filename)

        # Se il tipo di file non e' trovato, allora gli assegno come tipo di file il piu' generico possibile
        if filetype is None:
            filetype = 'application/octet-stream'

        # Response e' una classe che contiene appunto la risposta di un server a una richiesta HTTP
        res = Response(content_type=filetype)

        # Assegno al body della risposta cio' che riesco a leggere dalla pagina web
        res.body = open(filename, 'rb').read()
        return res

    def get_root(self, req, **_kwargs):
        return self.get_file(req, None)

    def get_file(self, req, filename, **_kwargs):
        if (filename == "" or filename is None):
            filename = "index.html"
        try:
            filename = os.path.join(self.directory, filename)
            return self.make_response(filename)
        except IOError:
            return Response(status=400)


class WebRestApi(app_manager.RyuApp):
    _CONTEXTS = {'wsgi': WSGIApplication}  # _CONTEXTS e' un dizionario: in questo caso la parola wsgi e' associata ad un'istanza WSGIApplication

    # a kwargs e' passato proprio _CONTEXTS, come si vedra'...
    def __init__(self, *args, **kwargs):
        super(WebRestApi, self).__init__(*args, **kwargs)

        # ora! infatti, qui si assegna alla variabile wsgi l'elemento associato alla parola wsgi definita in _CONTEXTS, quindi l'istanza di WSGIApplication
        wsgi = kwargs['wsgi']

        # da cui si ottiene l'istanza del mapper, che connette nelle istruzioni successive gli indirizzi web alla relativa pagina da caricare
        mapper = wsgi.mapper

        # specificatamente:
        # il primo argomento individua il nome della rotta
        # il secondo argomento individua il modo in cui solitamente si presentano gli URL
        # il terzo argomento individua il controller che gestira' le richieste in arrivo
        # il quarto argomento individua l'azione che il controller eseguira' per la richiesta in arrivo
        # il quinto argomento individua le ulteriori condizioni per cui la richiesta arrivata fa match con quelle che si attendono
        # P.S.: dict e' una funzione che permette di scrivere le condizioni nel modo opportuno, ovvero, cosi' {'method':GET}
        mapper.connect('web', '/web/{filename:.*}',
                       controller=WebController, action='get_file',
                       conditions=dict(method=['GET']))

        mapper.connect('web', '/',
                       controller=WebController, action='get_root',
                       conditions=dict(method=['GET']))
