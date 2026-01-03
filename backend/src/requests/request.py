from typing import Optional

from requests.exceptions import InvalidDecoding
from requests.schema import RequestMethod, RequestProtocol


class Request:
    def __init__(self):
        self.method: RequestMethod
        self.target: str = ""
        self.protocol: RequestProtocol
        self.headers: dict = {}
        self.body: Optional[dict] = None

    def parse(self, raw_data: bytes):
        try:
            request = raw_data.decode("utf-8")
        except UnicodeDecodeError:
            raise InvalidDecoding()
