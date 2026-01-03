from typing import Optional

from requests.exceptions import InvalidDecoding
from requests.schema import RequestMethod, RequestProtocol


class Request:
    def __init__(self, raw_data: bytes):
        self.method: RequestMethod
        self.target: str
        self.protocol: RequestProtocol
        self.headers: dict = {}
        self.body: Optional[bytes]

        try:
            request_headers, self.body = raw_data.split(b"\r\n\r\n", maxsplit=1)
            request_headers = request_headers.decode("utf-8")  # decode only headers
        except UnicodeDecodeError:
            raise InvalidDecoding()

        request_headers = request_headers.splitlines()

        # parse start-line: <METHOD> <TARGET> <PROTOCOL>
        start_line = request_headers.pop(0)
        self.method, self.target, self.protocol = start_line.split(" ")

        for header in request_headers:
            key, value = header.split(": ", maxsplit=1)
            self.headers[key] = value
