from typing import Dict, Optional

from request.exceptions import (
    InvalidHTTPHeaders,
    InvalidHTTPMethod,
    InvalidHTTPProtocol,
)
from request.schema import HTTPRequestMethod
from server.schema import HTTPProtocol


class HTTPRequest:
    method: HTTPRequestMethod
    url: str
    protocol: HTTPProtocol
    headers: Dict[str, str]
    body: Optional[str]

    def __init__(self, method, url, headers):
        self.headers: Dict[str, str] = {}
        self.body = None

    # TODO: free function return headers, url, body and methods, verify protocol
    def parse_headers(self, request_headers: str):
        request_headers = request_headers.splitlines()

        # parse request line: <METHOD> <TARGET> <PROTOCOL>
        request_line = request_headers.pop(0)
        request_line = request_line.split(" ")

        for header in request_headers:
            try:
                key, value = header.split(": ", maxsplit=1)
                self.headers[key] = value
            except ValueError:
                raise InvalidHTTPHeaders()

        try:
            self.method = HTTPRequestMethod(request_line[0])
        except ValueError:
            raise InvalidHTTPMethod(request_line[0])

        self.url = request_line[1]

        try:
            self.protocol = HTTPProtocol(request_line[2])
        except ValueError:
            raise InvalidHTTPProtocol(request_line[2])

    # TODO: think about writing body to a file and process from there
    def parse_body(self, request_body: str):
        self.body = request_body if request_body else None
