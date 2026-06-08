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
    InvalidBodyLength,
    InvalidContentLength,
    InvalidDecoding,
    InvalidRequest,
    InvalidTransferEncoding,
    UnspecifiedBodyLength,
    UnsupportedTransferEncoding, BodyTooLarge,
)
from server.tcp_server import TCPServer

logger = logging.getLogger(__name__)


class HTTPServer(TCPServer):
    MAX_BODY_SIZE = 1 * 1024 * 1024

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
            request = HTTPRequest(method, url, protocol, headers)
            response.set_protocol(protocol)

            case_insensitive_headers = {key.lower(): value for key, value in request.headers.items()}

            # since data might arrive in chunks, parsing the body requires us to either:
            # 1. receive a zero-length chunk Transfer-Encoding: Chunked
            # 2. know how long it is via Content-Length
            # 3. if none is present, assume no body

            transfer_encoding = case_insensitive_headers.get("transfer-encoding", None)
            content_length = case_insensitive_headers.get("content-length", None)

            # TODO: Wrong Chunked Parsing:
            #  1. Need to parse each chunk as declared on length prefix in hex
            #  2. Transfer-Encoding can be a list where 'chunked' must be the last element
            if transfer_encoding is not None:
                if transfer_encoding.lower() == "chunked":
                    while True:
                        chunk_data = client_connection.recv(1024)
                        if len(chunk_data) == 0:
                            break
                        body += chunk_data
                elif transfer_encoding.lower() in ("compress", "deflate", "gzip"):
                    raise UnsupportedTransferEncoding(transfer_encoding=transfer_encoding)
                else:
                    raise InvalidTransferEncoding(transfer_encoding=transfer_encoding)

            # TODO: Content-Length Improvements:
            #  1. Several 'Content-Length' can be sent, should '400 Bad Request' if they differ.
            elif content_length is not None:  # "Content-Length" is present
                try:
                    content_length = int(content_length)
                except ValueError:  # can't conver to integer, like empty string
                    raise InvalidContentLength(content_length=content_length)
                else:  # can convert to integer but still invalid like negative number
                    if content_length < 0:
                        raise InvalidContentLength(content_length=content_length)
                    elif content_length > self.MAX_BODY_SIZE:
                        raise BodyTooLarge(max_body_size=self.MAX_BODY_SIZE, content_length=content_length)

                if content_length == 0:
                    body = b""
                else:
                    while len(body) < content_length:
                        chunk_data = client_connection.recv(1024)
                        if not chunk_data:
                            break
                        body += chunk_data

                    if len(body) < content_length:
                        raise InvalidBodyLength(body_length=len(body), expected_length=content_length)
                    else:
                        body = body[:content_length] if content_length > 0 else b""

            elif request.method in (HTTPRequestMethod.POST, HTTPRequestMethod.PUT, HTTPRequestMethod.PATCH):
                raise UnspecifiedBodyLength(method=request.method)

            try:
                body = body.decode(encoding="UTF-8", errors="strict") if body else None
            except UnicodeDecodeError:
                raise InvalidDecoding()
            else:
                request.parse_body(body)

            request_handler = self.resolve_route(url=url, method=method)

            if request_handler:
                body = request_handler()
                response.set_status_code(status_code=HTTPResponseStatusCode.HTTP_200)
                response.set_body(body=body.data, content_type=body.content_type)
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
