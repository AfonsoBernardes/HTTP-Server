from datetime import datetime, timezone
from typing import Dict, Optional

from response.schema import HTTPResponseStatus
from server.schema import HTTPProtocol


class HTTPResponse:
    protocol: HTTPProtocol
    status_code: HTTPResponseStatus
    headers: Dict[str, str]
    body: Optional[str]

    def __init__(self, http_protocol: HTTPProtocol) -> None:
        self.protocol = http_protocol
        self.headers = {
            "Server": "Afonso's Server",
            "Content-Type": "application/json",  # TODO: Which type should I return? JSON and dela with any frontend elsewhere?
        }

    # TODO: too many setters/ getters?
    def set_status_code(self, status_code: HTTPResponseStatus):
        self.status_code = status_code

    def get_status_line(self) -> str:
        status_line = f"{self.protocol} {self.status_code}\r\n"
        return status_line

    def set_headers(self, extra_headers: Optional[Dict[str, str]] = None):
        self.headers["Date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        self.headers["Content-Length"] = str(len(self.body))

        if extra_headers:
            self.headers.update(extra_headers)

    def get_headers(self) -> str:
        response_headers = "".join(
            f"{header_name}: {header_value}\r\n" for header_name, header_value in self.headers.items()
        )
        return response_headers

    def set_body(self, body: str):
        self.body = body

    def get_body(self) -> str:
        return self.body
