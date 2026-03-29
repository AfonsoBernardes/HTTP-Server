from typing import Dict, Optional, Tuple

from request.exceptions import (
    InvalidHTTPHeaders,
    InvalidHTTPMethod,
    InvalidHTTPProtocol,
)
from request.schema import HTTPRequestMethod
from server.schema import HTTPProtocol


def parse_headers(request_headers: str) -> Tuple[
    HTTPRequestMethod,
    str,
    HTTPProtocol,
    Dict[str, str],
]:
    request_headers = request_headers.splitlines()

    # parse request line: <METHOD> <TARGET> <PROTOCOL>
    request_line = request_headers.pop(0)
    request_line = request_line.split(" ")

    headers = {}
    for header in request_headers:
        try:
            key, value = header.split(": ", maxsplit=1)
            headers[key] = value
        except ValueError:
            raise InvalidHTTPHeaders()

    try:
        method = HTTPRequestMethod(request_line[0])
    except ValueError:
        raise InvalidHTTPMethod(request_line[0])

    url = request_line[1]

    try:
        protocol = HTTPProtocol(request_line[2])
    except ValueError:
        raise InvalidHTTPProtocol(request_line[2])

    return method, url, protocol, headers


class HTTPRequest:
    method: HTTPRequestMethod
    url: str
    protocol: HTTPProtocol
    headers: Dict[str, str]
    body: Optional[str]

    def __init__(self, method, url, protocol, headers):
        self.method = method
        self.url = url
        self.protocol = protocol
        self.headers = headers
        self.body = None

    # TODO: think about writing body to a file and process from there
    def parse_body(self, request_body: str):
        self.body = request_body if request_body else None
