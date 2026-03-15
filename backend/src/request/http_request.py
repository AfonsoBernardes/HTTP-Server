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
    target: str
    protocol: HTTPProtocol
    headers: Dict[str, str]
    body: Optional[str]

    def __init__(self):
        self.headers: Dict[str, str] = {}
        self.body = None

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

        self.target = request_line[1]

        try:
            self.protocol = HTTPProtocol(request_line[2])
        except ValueError:
            raise InvalidHTTPProtocol(request_line[2])

    def parse_body(self, request_body: str):
        self.body = request_body if request_body else None
