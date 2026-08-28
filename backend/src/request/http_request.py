import re
from socket import socket
from typing import Dict, List, Optional, Tuple

from request.exceptions import (
    BodyTooLarge,
    DuplicateHTTPHeader,
    InvalidBodyLength,
    InvalidChunkSize,
    InvalidContentLength,
    InvalidHTTPHeaderKey,
    InvalidHTTPHeaders,
    InvalidHTTPMethod,
    InvalidHTTPProtocol,
    InvalidTransferEncoding,
    UnspecifiedBodyLength,
    UnsupportedTransferEncoding,
)
from request.schema import HTTPRequestMethod
from server.exceptions import InvalidDecoding
from server.schema import HTTPProtocol

INVALID_HEADER_KEY_CHARS = re.compile(r'[\x00-\x1f\x7f\s()<>@,;:\\"/\[\]?={}]')

SINGLE_VALUE_HEADERS = {
    "content-length",
    "content-type",
    "host",
    "authorization",
    "content-encoding",
}


def parse_headers(request_headers: str) -> Tuple[
    HTTPRequestMethod,
    str,
    HTTPProtocol,
    Dict[str, List[str]],
]:
    request_headers = request_headers.split("\r\n")

    # parse request line: <METHOD> <TARGET> <PROTOCOL>
    request_line = request_headers.pop(0)
    request_line = request_line.split(" ", maxsplit=3)

    headers = {}
    for header in request_headers:
        try:
            key, value = header.rsplit(":", maxsplit=1)

            invalid_char_match = INVALID_HEADER_KEY_CHARS.search(key)
            if invalid_char_match:
                invalid_char = invalid_char_match.group()
                raise InvalidHTTPHeaderKey(key=key, invalid_char=invalid_char)

            key = key.lower()
            value_list = [value.strip() for value in value.split(",")]

            for value in value_list:
                if key not in headers:
                    headers[key] = [value]
                else:
                    headers[key].append(value)
        except ValueError:
            raise InvalidHTTPHeaders()

    for key, value in headers.items():
        if key in SINGLE_VALUE_HEADERS and len(value) > 1:
            raise DuplicateHTTPHeader(header_key=key, num_values=len(value))

    try:
        method = HTTPRequestMethod(request_line[0])
    except ValueError:
        raise InvalidHTTPMethod(request_line[0])

    url = request_line[1]

    try:
        protocol = HTTPProtocol(request_line[2])
    except ValueError:
        raise InvalidHTTPProtocol(request_line[2])

    return method, url, protocol, headers


def parse_chunked_body(client_connection: socket, body_buffer: bytes) -> Optional[bytes]:
    raw_body = b""
    while True:
        while b"\r\n" not in body_buffer:
            body_buffer += client_connection.recv(1024)

        chunk_size_line, body_buffer = body_buffer.split(b"\r\n", maxsplit=1)

        chunk_size = chunk_size_line.split(b";", maxsplit=1)[0]  # ignore extensions
        try:
            chunk_size = chunk_size.decode(encoding="UTF-8", errors="strict")
            chunk_size = int(chunk_size, 16)
        except UnicodeDecodeError:
            raise InvalidDecoding()
        except:
            raise InvalidChunkSize(chunk_size)

        if chunk_size == 0:
            while True:
                while b"\r\n" not in body_buffer:
                    body_buffer += client_connection.recv(1024)

                # check if current request has trailer sections to be discarded
                current_request_line, body_buffer = body_buffer.split(b"\r\n", maxsplit=1)
                if current_request_line == b"":
                    # buffer is clean, contains only subsequent request data
                    break
            break

        body_chunk, body_buffer = read_exact(client_connection, body_buffer, chunk_size)
        raw_body += body_chunk
        _, body_buffer = read_exact(client_connection, body_buffer, 2)  # read and ignore delimiter

    # TODO: When keep-alive connections introduced, need to carry body_buffer, not discard it
    return raw_body


def read_exact(client_connection: socket, body_buffer: bytes, chunk_size: int) -> Tuple[bytes, bytes]:
    while len(body_buffer) < chunk_size:
        body_buffer += client_connection.recv(1024)

    body_chunk = body_buffer[:chunk_size]
    body_buffer = body_buffer[chunk_size:]

    return body_chunk, body_buffer


class HTTPRequest:
    method: HTTPRequestMethod
    url: str
    protocol: HTTPProtocol
    headers: Dict[str, List[str]]
    body: Optional[str]

    MAX_BODY_SIZE = 1 * 1024 * 1024

    def __init__(self, method, url, protocol, headers):
        self.method = method
        self.url = url
        self.protocol = protocol
        self.headers = headers
        self.body = None

    def parse_body(self, client_connection: socket, body_buffer: bytes) -> Optional[str]:
        # keys are already lower case from "parse_headers" function
        transfer_encoding = self.headers.get("transfer-encoding", None)
        content_length = self.headers.get("content-length", None)

        raw_body = b""
        if transfer_encoding is not None:
            if len(transfer_encoding) != 1:
                raise UnsupportedTransferEncoding(transfer_encoding=transfer_encoding)

            transfer_encoding = transfer_encoding[0]
            if transfer_encoding.lower() == "chunked":
                raw_body = parse_chunked_body(client_connection, body_buffer)
            elif transfer_encoding.lower() in ("compress", "deflate", "gzip"):
                raise UnsupportedTransferEncoding(transfer_encoding=transfer_encoding)
            else:
                raise InvalidTransferEncoding(transfer_encoding=transfer_encoding)

        elif content_length is not None:  # "Content-Length" is present
            content_length = content_length[0]
            try:
                content_length = int(content_length)  # "Content-Length" should be unique
            except ValueError:  # can't conver to integer, like empty string
                raise InvalidContentLength(content_length=content_length)
            else:  # can convert to integer but still invalid like negative number
                if content_length < 0:
                    raise InvalidContentLength(content_length=content_length)
                elif content_length > self.MAX_BODY_SIZE:
                    raise BodyTooLarge(max_body_size=self.MAX_BODY_SIZE, content_length=content_length)

            if content_length > 0:
                while len(body_buffer) < content_length:
                    chunk_data = client_connection.recv(1024)
                    if not chunk_data:
                        break
                    body_buffer += chunk_data

                if len(body_buffer) < content_length:
                    raise InvalidBodyLength(body_length=len(body_buffer), expected_length=content_length)
                else:
                    raw_body = body_buffer[:content_length]
                    # TODO: When keep-alive connections introduced, need to carry body_buffer, not discard it
                    body_buffer = body_buffer[content_length:]

        elif self.method in (HTTPRequestMethod.POST, HTTPRequestMethod.PUT, HTTPRequestMethod.PATCH):
            raise UnspecifiedBodyLength(method=self.method)

        try:
            self.body = raw_body.decode(encoding="UTF-8", errors="strict") if raw_body else None
        except UnicodeDecodeError:
            raise InvalidDecoding()

        return self.body
