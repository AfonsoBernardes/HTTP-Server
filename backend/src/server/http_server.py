from socket import socket
from typing import Callable, Dict, List, Optional

from request.http_request import HTTPRequest, parse_headers
from request.schema import HTTPRequestMethod
from response.http_response import HTTPResponse
from response.schema import HTTPResponseStatusCode
from router.exceptions import DuplicateRouter, DuplicateRouterPrefix
from router.http_router import HTTPRouter
from server.exceptions import InvalidBodyLength, InvalidDecoding, InvalidRequest
from server.tcp_server import TCPServer


class HTTPServer(TCPServer):
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
            route = free_router.get(url)
            if route:
                return router.resolve(sub_path, method)

        return None

    def handle_request(self, client_connection: socket) -> HTTPResponse:
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

        method, url, protocol, headers = parse_headers(request_headers=headers)
        request = HTTPRequest(method, url, protocol, headers)

        # since data might arrive in chunks, parsing the body requires us to either:
        # 1. receive a zero-length chunk Transfer-Encoding: Chunked
        # 2. know how long it is via Content-Length
        # 3. if none is present, Bad Request

        # TODO: I've seen that transfer-encoding is not universally supported in the request.
        # transfer_encoding = headers.get("Transfer-Encoding", None)
        # if transfer_encoding and transfer_encoding.lower() == "chunked":
        #     while True:
        #         chunk_data = client_connection.recv(1024)
        #         if len(chunk_data) == 0:
        #             break
        #         body += chunk_data

        content_length = int(request.headers.get("Content-Length", 0))
        if content_length:
            while len(body) < content_length:
                chunk_data = client_connection.recv(1024)
                if not chunk_data:
                    break
                body += chunk_data

            if len(body) < content_length:
                raise InvalidBodyLength(body_length=len(body), expected_length=content_length)
            else:
                body = body[:content_length] if content_length > 0 else b""

        try:
            body = body.decode(encoding="UTF-8", errors="strict") if body else None
        except UnicodeDecodeError:
            raise InvalidDecoding()
        else:
            request.parse_body(body)

        # TODO: let the server know about a routing table. Which routes matches the URL the request uses.
        # we need to resolve the route here, call the corresponding handler and that should be the response
        response = HTTPResponse(client_connection=client_connection, http_protocol=request.protocol)

        request_handler = self.resolve_route(url=url, method=method)

        body = None
        if request_handler:
            body = request_handler()
            response.set_status_code(status_code=HTTPResponseStatusCode.HTTP_200)
            response.set_headers({"Content-Type": body.content_type.value})
            body = body.data
        else:
            response.set_status_code(HTTPResponseStatusCode.HTTP_501)

        response.send_headers()

        response.set_body(body)
        response.send_body()

        return response
