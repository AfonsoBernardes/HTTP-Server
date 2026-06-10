import logging
from socket import socket
from typing import Callable, Dict, List, Optional

from api.schema import ContentType
from displayable_exceptions.http_exception import HTTPServerException
from request.http_request import HTTPRequest, parse_headers
from request.schema import HTTPRequestMethod
from response.http_response import HTTPResponse
from response.schema import HTTPResponseStatusCode
from router.exceptions import DuplicateRouter, DuplicateRouterPrefix
from router.http_router import HTTPRouter
from server.exceptions import (
    InvalidDecoding,
    InvalidRequest,
)
from server.tcp_server import TCPServer

logger = logging.getLogger(__name__)


class HTTPServer(TCPServer):
    # MAX_BODY_SIZE = 1 * 1024 * 1024

    def __init__(self):
        super().__init__()
        self.prefixed_routers: Dict[str, HTTPRouter] = {}
        self.free_routers: List[HTTPRouter] = []

    def include_router(self, router: HTTPRouter, prefix: Optional[str] = None) -> None:
        if router in self.free_routers or router in self.prefixed_routers.values():
            raise DuplicateRouter()

        if prefix:
            if prefix in self.prefixed_routers:
                raise DuplicateRouterPrefix(prefix=prefix)
            self.prefixed_routers[prefix] = router
        else:
            self.free_routers.append(router)

    def resolve_route(self, url: str, method: HTTPRequestMethod) -> Optional[Callable]:
        for prefix in self.prefixed_routers.keys():
            if url.startswith(prefix):
                router = self.prefixed_routers[prefix]
                sub_path = url[len(prefix) :]

                return router.resolve(sub_path, method)

        for free_router in self.free_routers:
            if free_router.routes.get(url):
                return free_router.resolve(url, method)

        return None

    def handle_request(self, client_connection: socket) -> HTTPResponse:
        response = HTTPResponse(client_connection=client_connection)
        try:
            # data might arrive in chunks loop makes sure all headers are present in the request
            raw_data = b""
            while b"\r\n\r\n" not in raw_data:
                # receive data from the socket. The return value is a bytes object representing the data received.
                # maximum amount of data to be received at once is specified by bufsize.
                chunk_data = client_connection.recv(1024)
                if not chunk_data:
                    break
                raw_data += chunk_data

            try:
                headers, body = raw_data.split(b"\r\n\r\n", maxsplit=1)
                headers = headers.decode(encoding="UTF-8", errors="strict")  # decode only headers
            except UnicodeDecodeError:
                raise InvalidDecoding()
            except ValueError:
                raise InvalidRequest()

            # TODO: Review how we parse headers with whitespaces
            method, url, protocol, headers = parse_headers(request_headers=headers)
            http_request = HTTPRequest(method, url, protocol, headers)
            response.set_protocol(protocol)

            request_body = http_request.parse_body(client_connection=client_connection, body=body)

            request_handler = self.resolve_route(url=url, method=method)

            if request_handler:
                response_body = request_handler()
                response.set_status_code(status_code=HTTPResponseStatusCode.HTTP_200)
                response.set_body(body=response_body.data, content_type=response_body.content_type)
            else:
                response.set_status_code(HTTPResponseStatusCode.HTTP_404)

        except HTTPServerException as http_exception:
            logger.error(http_exception.message)
            response.set_status_code(http_exception.status_code)
            response.set_body({"error": http_exception.message}, content_type=ContentType.JSON)

        finally:
            response.send_headers()
            response.send_body()

        return response
