from pathlib import Path
from socket import socket

from request.http_request import HTTPRequest
from response.http_response import HTTPResponse
from response.schema import HTTPResponseStatusCode
from server.exceptions import InvalidBodyLength, InvalidDecoding, InvalidRequest
from server.tcp_server import TCPServer


class HTTPServer(TCPServer):
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

        method, url, headers, = parse_headers(headers)
        request = HTTPRequest(method, url, headers)

        # since data might arrive in chunks, parsing the body requires us to know how long it is
        content_length = int(request.headers.get("Content-Length", 0))
        while len(body) < content_length:
            chunk_data = client_connection.recv(1024)
            if not chunk_data:
                break
            body += chunk_data

        # TODO: What should happen if len(body) > content_length? Truncate?
        # Client will not always know content-length, no more data = end of request
        if len(body) != content_length:
            raise InvalidBodyLength(body_length=len(body), expected_length=content_length)

        try:
            body = body.decode(encoding="UTF-8", errors="strict") if body else None
        except UnicodeDecodeError:
            raise InvalidDecoding()
        else:
            request.parse_body(body)

        response = HTTPResponse(http_protocol=request.protocol)
        if request.method != "GET":
            return response.set_status_code(HTTPResponseStatusCode.HTTP_501_NOT_IMPLEMENTED)

        # TODO: how can I efficiently route a request based on the method? would a decorator help here?
        # let the server know about a routing table. Which routes matches the URL the request uses.
        response.set_status_code(status_code=HTTPResponseStatusCode.HTTP_200_OK)

        get_request_template = self.TEMPLATES_PATH / "get_request.html"
        with get_request_template.open(mode="r", encoding="utf-8") as template:
            response.set_body(template.read().format(server_name=response.headers["Server"]))

        status_line = response.get_status_line()
        response.set_headers()
        response_headers = response.get_headers()
        response_string = f"{status_line}\r\n{response_headers}\r\n\r\n{response.body}"

        # TODO: I feel like this should return an HTTPResponse, however, socket.send requires a string
        return response_string
