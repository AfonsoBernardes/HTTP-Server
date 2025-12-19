from gi.overrides import override

from server.tcp_server import TCPServer


class HTTPServer(TCPServer):
    @override
    def handle_error(self, request, client_address):
        pass