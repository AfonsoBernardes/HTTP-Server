from typing import Optional

from requests.exceptions import InvalidDecoding, InvalidHTTPMethod, InvalidHTTPProtocol
from requests.schema import RequestMethod, RequestProtocol


class Request:
    method: RequestMethod
    target: str
    protocol: RequestProtocol
    headers: dict
    body: Optional[bytes]

    def __init__(self, raw_data: bytes):
        try:
            request_headers, self.body = raw_data.split(b"\r\n\r\n", maxsplit=1)
            request_headers = request_headers.decode("utf-8")  # decode only headers
        except UnicodeDecodeError:
            raise InvalidDecoding()

        request_headers = request_headers.splitlines()

        # parse start-line: <METHOD> <TARGET> <PROTOCOL>
        start_line = request_headers.pop(0)
        start_line = start_line.split(" ")

        try:
            self.method = RequestMethod(start_line[0])
        except ValueError:
            raise InvalidHTTPMethod(start_line[0])

        self.target = start_line[1]

        try:
            self.protocol = RequestProtocol(start_line[2])
        except ValueError:
            raise InvalidHTTPProtocol(start_line[2])

        self.headers = {}
        for header in request_headers:
            key, value = header.split(": ", maxsplit=1)
            self.headers[key] = value
