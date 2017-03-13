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

from webob import Response

from ryu.ofproto import ofproto_v1_3
from ryu.app.wsgi import ControllerBase, WSGIApplication
import turnout

turnout_instance_name = 'turnout_app'

# REST API
#
# Configure packet in requests
#
# Accept req
# GET /rest/accept
#
# Deny req
# GET /rest/deny
#
# get all live communications
# GET /rest/communications
#

# Check se MAC e' valido


class TurnoutController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(TurnoutController, self).__init__(req, link, data, **config)
        self.turnout_app = data[turnout_instance_name]

    def list_communications(self, req, **_kwargs):
        body = self.turnout_app.list_communications()
        return Response(content_type='text/html', body=body)

    def list_routes(self, req, **_kwargs):
        body = self.turnout_app.list_routes()
        return Response(content_type='text/html', body=body)

    def set_route(self, req, **_kwargs):
        self.turnout_app.set_route(req.body)
        return Response(status=200)


class TurnoutRestApi(turnout.Turnout):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    _CONTEXTS = {
        'wsgi': WSGIApplication,
    }

    def __init__(self, *args, **kwargs):
        super(TurnoutRestApi, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(TurnoutController,
                      {turnout_instance_name: self})
        mapper = wsgi.mapper

        mapper.connect('routes', '/rest/routes',
                       controller=TurnoutController, action='list_routes',
                       conditions=dict(method=['GET']))

        mapper.connect('routes', '/rest/communications',
                       controller=TurnoutController, action='list_communications',
                       conditions=dict(method=['GET']))

        mapper.connect('routes', '/rest/set_route',
                       controller=TurnoutController, action='set_route',
                       conditions=dict(method=['POST']))
