from typing import Dict, List, Optional, Tuple

from request.exceptions import (
    DuplicateHTTPHeader,
    InvalidHTTPHeaders,
    InvalidHTTPMethod,
    InvalidHTTPProtocol,
)
from request.schema import HTTPRequestMethod
from server.schema import HTTPProtocol

SINGLE_VALUE_HEADERS = {
    "content-length",
    "content-type",
    "host",
    "authorization",
    "content-encoding",
}


def parse_headers(request_headers: str) -> Tuple[
    HTTPRequestMethod,
    str,
    HTTPProtocol,
    Dict[str, List[str]],
]:
    request_headers = request_headers.splitlines()

    # parse request line: <METHOD> <TARGET> <PROTOCOL>
    request_line = request_headers.pop(0)
    request_line = request_line.split(" ")

    headers = {}
    for header in request_headers:
        try:
            key, value = header.split(": ", maxsplit=1)

            key = key.lower()
            value_list = [value.strip() for value in value.split(",")]

            for value in value_list:
                if key not in headers:
                    headers[key] = [value]
                else:
                    headers[key].append(value)
        except ValueError:
            raise InvalidHTTPHeaders()

    for key, value in headers.items():
        if key in SINGLE_VALUE_HEADERS and len(value) > 1:
            raise DuplicateHTTPHeader(header_key=key, num_values=len(value))

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
    headers: Dict[str, str | List[str]]
    body: Optional[str]

    def __init__(self, method, url, protocol, headers):
        self.method = method
        self.url = url
        self.protocol = protocol
        self.headers = headers
        self.body = None

    # TODO: think about writing body to a file and process from there
    def parse_body(self, request_body: Optional[str]):
        self.body = request_body if request_body else None
