# -*- coding: utf-8 -*-
"""Mirai Worm Honeycomb Service."""
import time
import errno
import socket
from collections import defaultdict

import gevent
import gevent.server
from telnetsrv.green import TelnetHandler, command

from base_service import ServerCustomService
from custom_pool import CustomPool


DEFAULT_TIMEOUT = 60  # Use to timeout the connection
POOL = 10
PORT = 23
IP_ADDRESS = "0.0.0.0"

MIRAI_DETECTED_EVENT_TYPE = "mirai_detection"
BUSYBOX_TELNET_INTERACTION_EVENT_TYPE = "busybox_telnet_execution"
BUSYBOX_TELNET_AUTHENTICATION = "busybox_telnet_authentication"
BUSYBOX_COMMAND_DESCRIPTION = "Command executed"

# Fields
EVENT_TYPE = "event_type"
CMD = "cmd"
USERNAME = "username"
PASSWORD = "password"
DESCRIPTION = "event_description"
ORIGINATING_IP = "originating_ip"
ORIGINATING_PORT = "originating_port"

DDOS_NAME = "Mirai"
COMMANDS = {
    "ECCHI": "ECCHI: applet not found",
    "ps": "1 pts/21   00:00:00 init",
    "cat /proc/mounts": "tmpfs /run tmpfs rw,nosuid,noexec,relatime,size=1635616k,mode=755 0 0",
    "echo -e \\x6b\\x61\\x6d\\x69/dev > /dev/.nippon": "",
    "cat /dev/.nippon": "kami/dev",
    "rm /dev/.nippon": "",
    "echo -e \\x6b\\x61\\x6d\\x69/run > /run/.nippon": "",
    "cat /run/.nippon": "kami/run",
    "rm /run/.nippon": "",
    "cat /bin/echo": "\\x7fELF\\x01\\x01\\x01\\x03\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x02\\x00\\x08\\x00"
                     "\\x00\\x00\\x00\\x00"
}

OVERWRITE_COMMANDS = {}  # Use to overwrite default telnet command behavior crashing the handler (e.g. 'help')
OVERWRITE_COMMANDS_LIST = ["help"]  # Don't forget to update the list when adding new commands

BUSY_BOX = "/bin/busybox"
MIRAI_SCANNER_COMMANDS = ["shell", "sh", "enable"]


class MyTelnetHandler(TelnetHandler, object):
    """Custom Telnet Handler for Mirai."""

    WELCOME = "welcome"
    PROMPT = ">"
    authNeedUser = True
    authNeedPass = True

    custom_pool = None
    logger = None
    active_users = {}
    ips_command_executed = defaultdict(list)

    @command(OVERWRITE_COMMANDS_LIST)
    def telnet_commands_respond(self, params):
        """Respond to telnet command."""
        self.writeresponse(OVERWRITE_COMMANDS.get(self.input.raw, ""))

    @command(MIRAI_SCANNER_COMMANDS)
    def shell_respond(self, params):
        """Handle something trying to use a shell command."""
        self.writeresponse("")

    @command([BUSY_BOX])
    def handle_busybox(self, params):
        """Handle someone trying to use a Busybox command."""
        full_response = self._get_busybox_response(params)
        self.writeresponse(full_response)

    def authCallback(self, username, password):
        """Handle Authentication."""
        self.active_users[self.client_address] = {USERNAME: username, PASSWORD: password}

    def session_start(self):
        """Start the session."""
        self._send_alert(**{DESCRIPTION: "Session started", EVENT_TYPE: BUSYBOX_TELNET_AUTHENTICATION})

    def session_end(self):
        """End the session on log off."""
        self._send_alert(**{DESCRIPTION: "Session end", EVENT_TYPE: BUSYBOX_TELNET_AUTHENTICATION})
        self._disconnect()

    def _get_busybox_response(self, params):
        """Create the reply when an attacker tries to activate one of the busybox that we have a canned reply for."""
        response = ""
        full_command = " ".join(params)
        for cmd in full_command.split(";"):
            cmd = cmd.strip()
            # Check for busybox executable
            if cmd.startswith(BUSY_BOX):
                cmd = cmd.replace(BUSY_BOX, "")
                cmd = cmd.strip()
            response += COMMANDS.get(cmd, "") + "\n"
            self._send_alert(**{CMD: cmd, EVENT_TYPE: BUSYBOX_TELNET_INTERACTION_EVENT_TYPE})
            self._store_command(cmd)
        return response

    def _send_alert(self, **kwargs):
        """Report an alert to the framework."""
        kwargs.update({
            ORIGINATING_IP: self.client_address[0],
            ORIGINATING_PORT: self.client_address[1],
        })
        kwargs.update(self.active_users.get(self.client_address, {}))
        self.emit(kwargs)

    def _is_fingerprinted(self):
        """Check to see if we correctly identified a Mirai instance."""
        if all([self.ips_command_executed[self.client_address[0]].count(cmd) > 0 for cmd in COMMANDS]):
            self._send_alert(**{EVENT_TYPE: MIRAI_DETECTED_EVENT_TYPE})
            self.ips_command_executed.pop(self.client_address[0], None)
        else:
            self.logger.debug("No fingerprint for ip %s with executed commands %s",
                              self.client_address, self.ips_command_executed[self.client_address[0]])

    def _store_command(self, cmd):
        self.logger.debug(
            "[%s:%d] executed: %s", self.client_address[0], self.client_address[1], cmd.strip())

        self.ips_command_executed[self.client_address[0]].append(cmd)
        self._is_fingerprinted()

    def inputcooker(self):
        """Cook the input."""
        try:
            super(MyTelnetHandler, self).inputcooker()
        except socket.timeout:
            self.custom_pool.remove_connection(str(self.client_address[0]) + ":" + str(self.client_address[1]))
            self.logger.debug("[%s:%d] session timed out", self.client_address[0], self.client_address[1])
            self.finish()
            self._disconnect()
        except socket.error as e:
            if e.errno != errno.EBADF:  # file descriptor error
                raise
            else:
                pass

    def _disconnect(self):
        """Handle a client disconnecting from the server."""
        self.active_users.pop(self.client_address, None)
        self.ips_command_executed.pop(self.client_address[0], None)


class MiraiWormMonitorService(ServerCustomService):
    """Mirai Worm Monitor Honeycomb Service."""

    def __init__(self, *args, **kwargs):
        super(MiraiWormMonitorService, self).__init__(*args, **kwargs)
        self.server = None

    def __str__(self):
        return "MiraiWormMonitor"

    def on_server_shutdown(self):
        """Shut down gracefully."""
        if not self.server:
            return
        self.server.stop()

    def on_server_start(self):
        """Initialize service."""
        socket.setdefaulttimeout(DEFAULT_TIMEOUT)
        custom_pool = CustomPool(self.logger, POOL)

        handler = MyTelnetHandler
        handler.custom_pool = custom_pool
        handler.logger = self.logger
        handler.emit = self.add_alert_to_queue

        self.server = gevent.server.StreamServer(
            (IP_ADDRESS, PORT),
            handler.streamserver_handle,
            spawn=custom_pool)

        self.signal_ready()
        self.server.serve_forever()

    def test(self):
        """Trigger service alerts and return a list of triggered event types."""
        def _send(data):
            client_socket.send(data)

        def _wait(data):
            d = b""
            while data not in d:
                time.sleep(0.1)
                d += client_socket.recv(65536)
                # self.logger.info(d)

        event_types = []
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(2)
        client_socket.connect(("127.0.0.1", PORT))
        _wait(b"Username:")
        _send(b"my_username\r\n")

        _wait(b"Password:")
        _send(b"mypass\r\n")

        _wait(b">")
        event_types.append(BUSYBOX_TELNET_AUTHENTICATION)
        for cmd in COMMANDS:
            event_types.append(BUSYBOX_TELNET_INTERACTION_EVENT_TYPE)
            _send("{} {}\r\n".format(BUSY_BOX, cmd).encode())
            _wait(b">")

        event_types.append(MIRAI_DETECTED_EVENT_TYPE)
        _send(b"bye\r\n")
        _wait(b"Goodbye")
        return event_types


service_class = MiraiWormMonitorService
