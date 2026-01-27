from typing import Optional

from requests.exceptions import (
    InvalidDecoding,
    InvalidHTTPHeaders,
    InvalidHTTPMethod,
    InvalidHTTPProtocol,
    InvalidRequest,
)
from requests.schema import HTTPRequestMethod, HTTPRequestProtocol


class HTTPRequest:
    method: HTTPRequestMethod
    target: str
    protocol: HTTPRequestProtocol
    headers: dict[str, str]
    body: Optional[bytes]

    def __init__(self, raw_data: bytes):
        self.parse_request(raw_data)

    def parse_request(self, raw_data: bytes):
        try:
            request_headers, request_body = raw_data.split(b"\r\n\r\n", maxsplit=1)
            request_headers = request_headers.decode("utf-8")  # decode only headers
        except UnicodeDecodeError:
            raise InvalidDecoding()
        except ValueError:
            raise InvalidRequest()
        else:
            self.body = request_body if request_body else None
            request_headers = request_headers.splitlines()

        # parse start-line: <METHOD> <TARGET> <PROTOCOL>
        start_line = request_headers.pop(0)
        start_line = start_line.split(" ")

        try:
            self.method = HTTPRequestMethod(start_line[0])
        except ValueError:
            raise InvalidHTTPMethod(start_line[0])

        self.target = start_line[1]

        try:
            self.protocol = HTTPRequestProtocol(start_line[2])
        except ValueError:
            raise InvalidHTTPProtocol(start_line[2])

        self.headers = {}
        for header in request_headers:
            try:
                key, value = header.split(": ", maxsplit=1)
                self.headers[key] = value
            except ValueError:
                raise InvalidHTTPHeaders()
