from typing import Dict, Optional

from response.schema import HTTPResponseStatus
from server.schema import HTTPProtocol


class HTTPResponse:
    protocol: HTTPProtocol
    status_code: HTTPResponseStatus
    headers: Dict[str, str]
    body: Optional[str]

    def __init__(self):
        self.headers = {
            "Server": "Afonso's Server",
            "Content-Type": "text/html",
        }

    def get_status_line(self, status_code: int) -> str:
        if status_code not in self.STATUS_CODES:
            raise Exception(f"invalid status code: '{status_code}'")

        status_line = f"HTTP/1.1 {status_code} {self.STATUS_CODES[status_code]}\r\n"
        return status_line