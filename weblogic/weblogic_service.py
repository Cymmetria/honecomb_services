# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from SocketServer import ThreadingMixIn

import weblogic_server
from base_service import ServerCustomService

from six.moves.BaseHTTPServer import HTTPServer


WEBLOGIC_PORT = 8000
EVENT_TYPE_FIELD_NAME = 'event_type'
WEBLOGIC_ALERT_TYPE_NAME = 'oracle_weblogic_rce'
ORIGINATING_IP_FIELD_NAME = 'originating_ip'
ORIGINATING_PORT_FIELD_NAME = 'originating_port'
CMD_FIELD_NAME = 'cmd'


class NonBlockingHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class OracleWebLogicService(ServerCustomService):
    def __init__(self, *args, **kwargs):
        super(OracleWebLogicService, self).__init__(*args, **kwargs)
        self.httpd = None

    def alert(self, request, payload):
        params = {
            EVENT_TYPE_FIELD_NAME: WEBLOGIC_ALERT_TYPE_NAME,
            ORIGINATING_IP_FIELD_NAME: request.client_address[0],
            ORIGINATING_PORT_FIELD_NAME: request.client_address[1],
            CMD_FIELD_NAME: ' '.join(payload),
        }
        self.add_alert_to_queue(params)

    def on_server_start(self):
        self.logger.info("Oracle Weblogic service started on port: %d", WEBLOGIC_PORT)

        requestHandler = weblogic_server.WebLogicHandler
        requestHandler.alert_function = self.alert
        requestHandler.logger = self.logger

        self.httpd = NonBlockingHTTPServer(('0.0.0.0', WEBLOGIC_PORT), requestHandler)

        self.signal_ready()
        self.httpd.serve_forever()

    def on_server_shutdown(self):
        if self.httpd:
            self.logger.info("Oracle Weblogic service stopped")
            self.httpd.shutdown()

    def __str__(self):
        return "Oracle Weblogic"


service_class = OracleWebLogicService
