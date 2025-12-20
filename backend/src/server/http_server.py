from datetime import datetime, timezone

from server.tcp_server import TCPServer


class HTTPServer(TCPServer):
    headers = {
        "Server": "Afonso's Server",
        "Content-Type": "text/html",
    }

    STATUS_CODES = {
        200: "OK",
        404: "Not Found",
    }

    def handle_request(self, data) -> str:
        status_line = self.get_status_line(status_code=200)
        response_headers = self.get_response_headers()

        response_body = """
        <html>
            <body>
                <h1>Request received!</h1>
            <body>
        </html>
        """

        response = f"{status_line}{response_headers} \r\n {response_body}"
        return response

    def get_status_line(self, status_code: int) -> str:
        if status_code not in self.STATUS_CODES:
            raise Exception(f"invalid status code: '{status_code}'")

        status_line = f"HTTP/1.1 {status_code} {self.STATUS_CODES[status_code]}\r\n"
        return status_line

    def get_response_headers(self, extra_headers: dict[str, str] = None) -> str:
        headers = self.headers.copy()
        headers["Date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

        if extra_headers:
            headers.update(extra_headers)

        response_headers = "\r\n".join(
            f"{header_name}: {header_value}" for header_name, header_value in headers.items()
        )
        return response_headers
