from datetime import datetime, timezone
from pathlib import Path
from socket import socket

from server.exceptions import InvalidDecoding, InvalidRequest, InvalidBodyLength
from request.http_request import HTTPRequest
from server.tcp_server import TCPServer


class HTTPServer(TCPServer):
    HEADERS = {
        "Server": "Afonso's Server",
        "Content-Type": "text/html",
    }

    STATUS_CODES = {
        200: "OK",
        404: "Not Found",
    }

    TEMPLATES_PATH = Path(__file__).parent.parent / "templates"

    def handle_request(self, client_connection: socket) -> str:
        # loop makes sure all headers are present in the request
        raw_data = b""
        while b"\r\n\r\n" not in raw_data:
            # receive data from the socket. The return value is a bytes object representing the data received.
            # maximum amount of data to be received at once is specified by bufsize.
            chunk_data = client_connection.recv(1024)
            if not chunk_data:
                break
            raw_data += chunk_data

        try:
            headers, body = raw_data.split(b"\r\n\r\n", maxsplit=1)
            headers = headers.decode(encoding="UTF-8", errors="strict")  # decode only headers
        except UnicodeDecodeError:
            raise InvalidDecoding()
        except ValueError:
            raise InvalidRequest()

        request = HTTPRequest()
        request.parse_headers(headers)

        # since data might arrive in chunks, parsing the body requires us to know how long it is
        content_length = int(request.headers.get("Content-Length", 0))
        while len(body) < content_length:
            chunk_data = client_connection.recv(1024)
            if not chunk_data:
                break
            body += chunk_data

        if len(body) != content_length:
            raise InvalidBodyLength(body_length=len(body), expected_length=content_length)

        try:
            body = body.decode(encoding="UTF-8", errors="strict") if body else None
        except UnicodeDecodeError:
            raise InvalidDecoding()

        request.parse_body(body)

        # TODO: need to parse request to check URL, get method and route action.
        # how can I efficiently route a request based on the method? would a decorator help here?
        status_line = self.get_status_line(status_code=200)
        response_headers = self.get_response_headers()

        get_request_template = self.TEMPLATES_PATH / "get_request.html"
        with get_request_template.open(mode="r", encoding="utf-8") as template:
            response_body = template.read().format(server_name=self.HEADERS["Server"])

        response = f"{status_line}{response_headers}\r\n{response_body}"
        return response

    def get_status_line(self, status_code: int) -> str:
        if status_code not in self.STATUS_CODES:
            raise Exception(f"invalid status code: '{status_code}'")

        status_line = f"HTTP/1.1 {status_code} {self.STATUS_CODES[status_code]}\r\n"
        return status_line

    def get_response_headers(self, extra_headers: dict[str, str] = None) -> str:
        headers = self.HEADERS.copy()
        headers["Date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

        if extra_headers:
            headers.update(extra_headers)

        response_headers = "".join(
            f"{header_name}: {header_value}\r\n" for header_name, header_value in headers.items()
        )
        return response_headers
