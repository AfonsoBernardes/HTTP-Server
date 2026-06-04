import json
from datetime import datetime, timezone
from socket import socket
from typing import Any, Dict, Optional

from api.schema import ContentType
from response.exceptions import InvalidBody, InvalidResponseHeader
from response.schema import HTTPResponseStatusCode
from server.schema import HTTPProtocol


class HTTPResponse:
    protocol: HTTPProtocol
    status_code: HTTPResponseStatusCode
    headers: Dict[str, str]
    body: str

    def __init__(self, client_connection: socket):
        self.client_connection = client_connection
        self.headers = {"Server": "Afonso's Server"}
        self.body = ""

    def set_protocol(self, protocol: HTTPProtocol):
        self.protocol = protocol

    def set_status_code(self, status_code: HTTPResponseStatusCode):
        self.status_code = status_code

    def set_headers(self, extra_headers: Optional[Dict[str, str]] = None):
        self.headers["Date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

        if extra_headers:
            try:
                self.headers.update(extra_headers)
            except (TypeError, ValueError):
                raise InvalidResponseHeader()

    def get_headers(self) -> str:
        response_headers = "".join(
            f"{header_name}: {header_value}\r\n" for header_name, header_value in self.headers.items()
        )
        return response_headers

    # should be able to send header section to the client before the full body
    def send_headers(self):
        status_line = f"{self.protocol.value} {self.status_code}"
        response_headers = self.get_headers()

        header_section = f"{status_line}\r\n{response_headers}\r\n\r\n"
        self.client_connection.send(header_section.encode("utf-8"))

    @staticmethod
    def _transform_body(body: Optional[Any], content_type: ContentType) -> str:
        if content_type == ContentType.JSON:
            return json.dumps(body)
        else:
            return str(body) if body else ""

    def set_body(self, body: Any, content_type: ContentType):
        try:
            self.headers["Content-Type"] = content_type.value
            self.body = self._transform_body(body, content_type)
        except (TypeError, ValueError):
            raise InvalidBody(body, content_type)

    def get_body(self) -> str:
        return self.body

    def send_body(self):
        self.client_connection.send(self.body.encode("utf-8"))
