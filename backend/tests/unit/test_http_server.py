import logging
import re
from typing import Optional, Any

import pytest
from asserts import assert_equal, assert_in, assert_is_none

from conftest import FakeSocket
from request.exceptions import (
    DuplicateHTTPHeader,
    InvalidHTTPHeaders,
    InvalidHTTPMethod,
    InvalidHTTPProtocol,
    UnsupportedTransferEncoding,
    InvalidTransferEncoding,
    InvalidContentLength,
    InvalidBodyLength,
    BodyTooLarge,
    UnspecifiedBodyLength, InvalidChunkSize,
)
from request.schema import HTTPRequestMethod
from router.exceptions import DuplicateRouterPrefix, DuplicateRouter
from router.http_router import HTTPRouter
from server.exceptions import InvalidDecoding, InvalidRequest
from server.http_server import HTTPServer


class TestServerHeaderHandling:
    @pytest.mark.parametrize(
        "request_headers",
        [
            b"GET / HTTP/1.1\r\n\r\n",
            b"GET / HTTP/1.1\r\nContent-Length: 0\r\n\r\n",
            b"DELETE / HTTP/1.1\r\n\r\n",
            b"HEAD / HTTP/1.1\r\nContent-Length: 0\r\n\r\n",
            b"POST / HTTP/1.1\r\nContent-Length: 1\r\n\r\nA",
            b"POST / HTTP/1.1\r\nTransfer-Encoding: Chunked\r\n\r\n0\r\n\r\n",
            b"PUT / HTTP/1.1\r\ncontent-length: 0\r\n\r\n",
            b"PUT / HTTP/1.1\r\ntransfer-encoding: chunked\r\n\r\n0\r\n\r\n",
            b"PATCH / HTTP/1.1\r\nCONTENT-LENGTH: 2\r\n\r\nAB",
            b"PATCH / HTTP/1.1\r\nTRANSFER-ENCODING: CHUNKED\r\n\r\n0\r\n\r\n"
        ],
    )
    @pytest.mark.asyncio
    async def test_should_handle_valid_request_with_case_insensitive_headers(self, request_headers: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            request_headers
        ])

        assert http_server.handle_request(fake_connection)

    @pytest.mark.parametrize(
        "request_headers",
        [
            b"GET / HTTP/1.1\r\n\r\n",
            b"GET / HTTP/1.1\r\nTransfer: chunked\r\n\r\n",
            b"PATCH / HTTP/1.1\r\ncontent: 1\r\n\r\nBody ignored"
            b"PATCH / HTTP/1.1\r\nencoding: chunked\r\n\r\nBody ignored"
            b"DELETE / HTTP/1.1\r\nLENGTH: A\r\n\r\n"
            b"DELETE / HTTP/1.1\r\nENCODING: A\r\n\r\n"
        ],
    )
    @pytest.mark.asyncio
    async def test_should_handle_valid_request_without_content_length_or_transfer_encoding_header(self, request_headers: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            request_headers
        ])

        assert http_server.handle_request(fake_connection)

    @pytest.mark.parametrize(
        "invalid_headers",
        [
            b"GET / HTTP/1.1",
            b"GET / HTTP/1.1\r\n",
            b"GET / HTTP/1.1\r\nHeader: Value\r\n"
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_without_two_line_breaks(self, caplog, invalid_headers: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_headers,
            b"",
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, InvalidRequest.status_code)
        assert_in(InvalidRequest().base_message, caplog.text)

    @pytest.mark.parametrize(
        "invalid_header_encoding",
        [
            b"GET / HTTP/1.1\r\nSomething: \xff\r\n\r\n",
            b"GET / HTTP/1.1\r\nSomething: \x80\r\n\r\n",
            b"GET / HTTP/1.1\r\nSomething: \xc3\r\n\r\n",
            b"GET / HTTP/1.1\r\nSomething: \xc3\x28\r\n\r\n",
            b"GET / HTTP/1.1\r\nSomething: \xf0\x28\x8c\xbc\r\n\r\n",
            b"GET / HTTP/1.1\r\nSomething: \xff\xfe\xfa\r\n\r\n",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_header_encoding(self, caplog, invalid_header_encoding: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_header_encoding,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, InvalidDecoding.status_code)
        assert_in(InvalidDecoding().base_message, caplog.text)

    @pytest.mark.parametrize(
        "invalid_headers",
        [
            b"GET / HTTP/1.1\r\nInvalid-Headers Test\r\n\r\n",
            b"GET / HTTP/1.1\r\nInvalidHeaders - Test\r\n\r\n",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_headers(self, caplog, invalid_headers: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_headers,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, InvalidHTTPHeaders.status_code)
        assert_in(InvalidHTTPHeaders().base_message, caplog.text)

    @pytest.mark.parametrize(
        "request_headers, header_key, num_values",
        [
            (b"POST / HTTP/1.1\r\nContent-Type: Test Server\r\nContent-Type: text/html\r\n\r\n", "content-type", 2),
            (b"POST / HTTP/1.1\r\nContent-Length: 0\r\ncontent-length: 0\r\n\r\n", "content-length", 2),
            (b"POST / HTTP/1.1\r\nHost: Host 1\r\nhost: Host 2\r\nHOST: Host3\r\n\r\n", "host", 3),
            (b"POST / HTTP/1.1\r\nAUTHORIZATION: BearerXYZ\r\nAuthorization: BearerZYX\r\n\r\n", "authorization", 2),
            (b"POST / HTTP/1.1\r\nContent-Encoding: gzip, compressed,deflate\r\n\r\n", "content-encoding", 3),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_disallowed_duplicate_headers(self, caplog, request_headers: bytes, header_key: str, num_values: int):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            request_headers,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, DuplicateHTTPHeader.status_code)
        assert_in(DuplicateHTTPHeader(header_key=header_key, num_values=num_values).base_message, caplog.text)

    @pytest.mark.parametrize(
        "invalid_headers, invalid_method",
        [
            (b" / HTTP/1.1\r\n\r\n", ""),
            (b"/ HTTP/1.1\r\n\r\n", "/"),
            (b"INVALID / HTTP/1.1\r\n\r\n", "INVALID"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_http_method(self, caplog, invalid_headers: bytes, invalid_method: str):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_headers,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, InvalidHTTPMethod.status_code)
        assert_in(InvalidHTTPMethod(method=invalid_method).base_message, caplog.text)

    @pytest.mark.parametrize(
        "invalid_headers, invalid_protocol",
        [
            (b"GET / HTTP/1.3\r\n\r\n", "HTTP/1.3"),
            (b"GET / HTTP/2\r\n\r\n", "HTTP/2"),
            (b"GET / INVALID\r\n\r\n", "INVALID"),
            (b"GET / \r\n\r\n", None),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_http_protocol(self, caplog, invalid_headers: bytes, invalid_protocol: str):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_headers,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, InvalidHTTPProtocol.status_code)
        assert_in(InvalidHTTPProtocol(protocol=invalid_protocol).base_message, caplog.text)

    @pytest.mark.parametrize(
        "request_line, unsupported_transfer_encoding",
        [
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: compress\r\n\r\n", "compress"),
            (b"PUT / HTTP/1.1\r\ntransfer-encoding: deflate\r\n\r\n", "deflate"),
            (b"PATCH / HTTP/1.1\r\nTRANSFER-ENCODING: gzip\r\n\r\n", "gzip"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_unsupported_transfer_encoding(self, caplog, request_line: bytes, unsupported_transfer_encoding: str):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            request_line,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, UnsupportedTransferEncoding.status_code)
        assert_in(UnsupportedTransferEncoding(transfer_encoding=unsupported_transfer_encoding).base_message, caplog.text)

    @pytest.mark.parametrize(
        "request_line, invalid_transfer_encoding",
        [
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: \r\n\r\n", ""),
            (b"PUT / HTTP/1.1\r\nTransfer-Encoding: ABC\r\n\r\n", "ABC"),
            (b"PATCH / HTTP/1.1\r\nTransfer-Encoding: 1\r\n\r\n", "1"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_transfer_encoding(self, caplog, request_line: bytes, invalid_transfer_encoding: str):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            request_line,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, InvalidTransferEncoding.status_code)
        assert_in(InvalidTransferEncoding(transfer_encoding=invalid_transfer_encoding).base_message, caplog.text)

    @pytest.mark.parametrize(
        "headers, invalid_content_length",
        [
            (b"GET / HTTP/1.1\r\nContent-Length: ABC\r\n\r\n", "ABC"),
            (b"GET / HTTP/1.1\r\nContent-Length: -1\r\n\r\n", -1),
            (b"GET / HTTP/1.1\r\nContent-Length: \r\n\r\n", None)
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_content_length(self, caplog, headers: bytes, invalid_content_length: Any):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            headers,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, InvalidContentLength.status_code)
        assert_in(InvalidContentLength(invalid_content_length).base_message, caplog.text)

    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_multiple_different_content_lengths(self, caplog):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            b"GET / HTTP/1.1\r\nContent-Length: 0\r\nContent-Length: 1\r\n\r\n",
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, DuplicateHTTPHeader.status_code)
        assert_in(DuplicateHTTPHeader(header_key="content-length", num_values=2).base_message, caplog.text)

    @pytest.mark.parametrize(
        "headers, large_content_length",
        [
            (b"GET / HTTP/1.1\r\nContent-Length: 9999999\r\n\r\n", 9999999),
            (b"GET / HTTP/1.1\r\nContent-Length: 1048577\r\n\r\n", 1048577)
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_too_large_content_length(self, caplog, headers: bytes, large_content_length: int):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            headers,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, BodyTooLarge.status_code)
        assert_in(BodyTooLarge(max_body_size=1024*1024, content_length=large_content_length).base_message, caplog.text)

    @pytest.mark.parametrize(
        "request_line, request_method",
        [
            (b"POST / HTTP/1.1\r\n\r\n", HTTPRequestMethod.POST),
            (b"PUT / HTTP/1.1\r\n\r\n", HTTPRequestMethod.PUT),
            (b"PATCH / HTTP/1.1\r\n\r\n", HTTPRequestMethod.PATCH),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_without_transfer_encoding_or_content_length(self, caplog, request_line: bytes, request_method: HTTPRequestMethod):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            request_line,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, UnspecifiedBodyLength.status_code)
        assert_in(UnspecifiedBodyLength(method=request_method).base_message, caplog.text)


class TestServerBodyHandling:
    @pytest.mark.parametrize(
        "bytes_request",
        [
            b"POST / HTTP/1.1\r\nContent-Length: 0\r\n\r\n",
            b"POST / HTTP/1.1\r\nContent-Length: 20\r\n\r\nCorrect body length.",
            b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n",
            b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nA\r\n0\r\n\r\n",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_handle_request_with_valid_body(self, bytes_request: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            bytes_request,
        ])

        assert http_server.handle_request(fake_connection)

    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_body_length(self, caplog):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            b"POST / HTTP/1.1\r\nContent-Length: 20\r\n\r\nShorter than twenty",
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, InvalidBodyLength.status_code)
        assert_in(InvalidBodyLength(body_length=19, expected_length=20).base_message, caplog.text)


    @pytest.mark.parametrize(
        "invalid_body_encoding",
        [
            b"POST / HTTP/1.1\r\nContent-Length: 1\r\n\r\n\xff",
            b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n1\r\n\xff\r\n0\r\n\r\n",
            b"POST / HTTP/1.1\r\nContent-Length: 1\r\n\r\n\x80",
            b"POST / HTTP/1.1\r\nContent-Length: 1\r\n\r\n\xc3",
            b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n4\r\n\xf0\x28\x8c\xbc\r\n0\r\n\r\n",
            b"POST / HTTP/1.1\r\nContent-Length: 3\r\n\r\n\xff\xfe\xfa",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_body_encoding(self, caplog, invalid_body_encoding: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_body_encoding,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, InvalidDecoding.status_code)
        assert_in(InvalidDecoding().base_message, caplog.text)


    @pytest.mark.parametrize(
        "invalid_body_encoding, invalid_chunk_size",
        [
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n\r\n\r\n", ""),
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n;extension=something\r\n\r\n", ""),
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\ng\r\nA\r\n0\r\n\r\n", b"g"),
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n 1\r\nA\r\n0\r\n\r\n", b" 1"),
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n1 \r\nA\r\n0\r\n\r\n", b"1 "),
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n-1\r\nA\r\n0\r\n\r\n", b"-1"),
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n+1\r\nA\r\n0\r\n\r\n", b"+1"),
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n1_a\r\nA\r\n0\r\n\r\n", b"1_a"),
            (b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n0x1\r\nA\r\n0\r\n\r\n", b"0x1"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_bchunk_size(self, caplog, invalid_body_encoding: bytes, invalid_chunk_size: str):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_body_encoding,
        ])

        with caplog.at_level(logging.ERROR):
            response = http_server.handle_request(fake_connection)

        assert_equal(response.status_code, InvalidChunkSize.status_code)
        assert_in(InvalidChunkSize(invalid_chunk_size).base_message, caplog.text)


class TestServerRouting:
    @pytest.mark.asyncio
    async def test_should_include_router_without_prefix(self):
        http_server = HTTPServer()
        router = HTTPRouter()

        http_server.include_router(router=router)
        assert_in(router, http_server.free_routers)

    @pytest.mark.asyncio
    async def test_should_include_router_with_valid_prefix(self):
        http_server = HTTPServer()
        router = HTTPRouter()
        prefix = "/test_prefix"

        http_server.include_router(prefix=prefix, router=router)

        assert_in(prefix, http_server.prefixed_routers)
        assert_equal(http_server.prefixed_routers[prefix], router)

    @pytest.mark.parametrize(
        "first_prefix, second_prefix",
        [
            (None, None),
            (None, "/second_prefix"),
            ("/first_prefix", None),
            ("/first_prefix", "/second_prefix"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_include_duplicate_router(self, first_prefix: Optional[str], second_prefix: Optional[str]):
        http_server = HTTPServer()
        router = HTTPRouter()

        http_server.include_router(prefix=first_prefix, router=router)

        if first_prefix:
            assert_in(first_prefix, http_server.prefixed_routers)
            assert_equal(http_server.prefixed_routers[first_prefix], router)
        else:
            assert_in(router, http_server.free_routers)

        expected_error_message = f"router already exists"
        with pytest.raises(DuplicateRouter, match=re.escape(expected_error_message)):
            http_server.include_router(prefix=second_prefix, router=router)

    @pytest.mark.asyncio
    async def test_should_fail_to_include_new_router_with_duplicate_prefix(self):
        http_server = HTTPServer()
        router = HTTPRouter()
        prefix = "/test_prefix"

        http_server.include_router(prefix=prefix, router=router)

        assert_in(prefix, http_server.prefixed_routers)
        assert_equal(http_server.prefixed_routers[prefix], router)

        new_router = HTTPRouter()
        expected_error_message = f"a router with prefix {prefix!r} already exists"
        with pytest.raises(DuplicateRouterPrefix, match=re.escape(expected_error_message)):
            http_server.include_router(prefix=prefix, router=new_router)

    @pytest.mark.parametrize(
        "http_method, url",
        [
            (request_method, "/") for request_method in HTTPRequestMethod
        ],
    )
    @pytest.mark.asyncio
    async def test_should_resolve_route_without_prefix(self, http_method: HTTPRequestMethod, url: str):
        http_server = HTTPServer()
        router = HTTPRouter()
        router.routes = {
            url: {
                http_method: lambda x: x,  # associate callable function to method
            }
        }

        http_server.include_router(router=router)
        assert_in(router, http_server.free_routers)

        result = http_server.resolve_route(url=url, method=http_method)
        assert_equal(result("Something"), "Something")

    @pytest.mark.parametrize(
        "http_method, url",
        [
            (request_method, "/") for request_method in HTTPRequestMethod
        ],
    )
    @pytest.mark.asyncio
    async def test_should_resolve_route_with_prefix(self, http_method: HTTPRequestMethod, url: str):
        http_server = HTTPServer()
        router = HTTPRouter()
        router.routes = {
            url: {
                http_method: lambda x: x,  # associate callable function to method
            }
        }

        prefix = "/test_prefix"
        http_server.include_router(prefix=prefix, router=router)

        assert_in(prefix, http_server.prefixed_routers)
        assert_equal(http_server.prefixed_routers[prefix], router)

        result = http_server.resolve_route(url=f"{prefix}{url}", method=http_method)

        assert_equal(result("Something"), "Something")

    @pytest.mark.parametrize(
        "prefix, bad_url",
        [
            (None, "/bad_url"),
            ("/test_prefix", "/not_right_prefix/")
        ],
    )
    @pytest.mark.asyncio
    async def test_should_resolve_route_to_none(self, prefix: Optional[str], bad_url: str):
        http_server = HTTPServer()
        router = HTTPRouter()
        router.routes = {
            "/": {
                HTTPRequestMethod.GET: lambda x: x,  # associate callable function to method
            }
        }

        http_server.include_router(prefix=prefix, router=router)

        if prefix:
            assert_in(prefix, http_server.prefixed_routers)
            assert_equal(http_server.prefixed_routers[prefix], router)
        else:
            assert_in(router, http_server.free_routers)

        result = http_server.resolve_route(url=bad_url, method=HTTPRequestMethod.GET)
        assert_is_none(result)
