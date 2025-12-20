from server.tcp_server import TCPServer


class HTTPServer(TCPServer):
    def handle_request(self, data) -> str:
        status_line = "HTTP/1.1 200 OK\r\n"
        response_body = """
        <html>
            <body>
                <h1>Request received!</h1>
            <body>
        </html>
        """

        response = f"{status_line} {response_body}"

        return response
