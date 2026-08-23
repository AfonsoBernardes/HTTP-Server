import re
from typing import Optional, Dict, List, Any

import pytest
from asserts import assert_equal, assert_raises

from conftest import FakeSocket
from request.exceptions import (
    InvalidHTTPMethod,
    InvalidHTTPProtocol,
    InvalidHTTPHeaders,
    DuplicateHTTPHeader,
    InvalidBodyLength,
    InvalidContentLength,
    BodyTooLarge,
    UnspecifiedBodyLength,
    UnsupportedTransferEncoding,
    InvalidTransferEncoding, InvalidHTTPHeaderKey,
)
from request.http_request import HTTPRequest, parse_headers
from request.schema import HTTPRequestMethod
from server.exceptions import InvalidDecoding
from server.schema import HTTPProtocol


class TestRequestMethod:
    EXPECTED_METHODS = ", ".join(method.value for method in HTTPRequestMethod)

    @pytest.mark.parametrize(
        "request_method",
        [
            request_method.value for request_method in HTTPRequestMethod
        ],
    )
    @pytest.mark.asyncio
    async def test_should_parse_request_with_valid_method(self, request_method: str):
        data = f"{request_method} / HTTP/1.1"

        method, url, protocol, headers = parse_headers(data)
        request = HTTPRequest(method, url, protocol, headers)

        assert_equal(request.method, HTTPRequestMethod(request_method))
        assert_equal(request.url, "/")
        assert_equal(request.protocol, HTTPProtocol.HTTP_1_1)
        assert_equal(request.headers, {})
        assert_equal(request.body, None)


    @pytest.mark.parametrize(
        "invalid_request_method, error_message",
        [
            (None, f"invalid HTTP method: expected [{EXPECTED_METHODS}], got 'None'"),
            ("", f"invalid HTTP method: expected [{EXPECTED_METHODS}], got None"),
            (" ", f"invalid HTTP method: expected [{EXPECTED_METHODS}], got None"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_parse_request_with_invalid_method(self, invalid_request_method, error_message: str):
        data = f"{invalid_request_method} / HTTP/1.1"

        with pytest.raises(InvalidHTTPMethod, match=re.escape(error_message)):
            parse_headers(data)



class TestRequestProtocol:
    EXPECTED_PROTOCOL = ", ".join(protocol.value for protocol in HTTPProtocol)

    @pytest.mark.parametrize(
        "request_protocol",
        [
            request_protocol.value for request_protocol in HTTPProtocol
        ],
    )
    @pytest.mark.asyncio
    async def test_should_parse_request_with_valid_protocol(self, request_protocol: str):
        data = f"GET / {request_protocol}"

        method, url, protocol, headers = parse_headers(data)
        request = HTTPRequest(method, url, protocol, headers)

        assert_equal(request.method, "GET")
        assert_equal(request.url, "/")
        assert_equal(request.protocol, HTTPProtocol(request_protocol))
        assert_equal(request.headers, {})
        assert_equal(request.body, None)


    @pytest.mark.parametrize(
        "invalid_request_protocol, error_message",
        [
            (None, f"invalid HTTP protocol: expected [{EXPECTED_PROTOCOL}], got 'None'"),
            ("", f"invalid HTTP protocol: expected [{EXPECTED_PROTOCOL}], got None"),
            (" ", f"invalid HTTP protocol: expected [{EXPECTED_PROTOCOL}], got None"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_parse_request_with_invalid_protocol(self, invalid_request_protocol, error_message: str):
        data = f"GET / {invalid_request_protocol}"

        with pytest.raises(InvalidHTTPProtocol, match=re.escape(error_message)):
            parse_headers(data)


class TestRequestHeadersParsing:
    @pytest.mark.parametrize(
        "request_headers, expected_headers",
        [
            # ("", {}),
            ("Header-Key: Header Value", {"header-key": ["Header Value"]}),
            ("Header-Key:Header Value", {"header-key": ["Header Value"]}),
            ("Header-Key: Header Value\r\nContent-Type: text/html", {"header-key": ["Header Value"], "content-type": ["text/html"]}),
            ("Header-Key: Header Value 1\r\nheader-key:Header Value 2\r\nContent-Type: text/html", {"header-key": ["Header Value 1" , "Header Value 2"], "content-type": ["text/html"]}),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_parse_valid_request_headers(self, request_headers: str, expected_headers: dict):
        data = f'GET / HTTP/1.1\r\n{request_headers}'

        method, url, protocol, headers = parse_headers(data)
        request = HTTPRequest(method, url, protocol, headers)

        assert_equal(request.method, HTTPRequestMethod.GET)
        assert_equal(request.url, "/")
        assert_equal(request.protocol, HTTPProtocol.HTTP_1_1)
        assert_equal(request.headers, expected_headers)

    @pytest.mark.parametrize(
        "invalid_header_key, invalid_char",
        [
            ("Header Key", " "),
            ("Header:Key", ":"),
            ("Header\nKey", "\\x0a"),
            ("Header\rKey", "\\x0d"),
            ("Header\tKey", "\\x09"),
            ("HeaderKey[", "["),
            ("HeaderKey]", "]"),
            ("HeaderKey\\", "\\"),
            ("HeaderKey/", "/"),
            ("HeaderKey<", "<"),
            ("HeaderKey>", ">"),
            ("HeaderKey@", "@"),
            ("HeaderKey,", ","),
            ("HeaderKey;", ";"),
            ("HeaderKey{", "{"),
            ("HeaderKey}", "}"),
            ("HeaderKey\x7f", "\\x7f"),


        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_parse_request_headers_with_invalid_characters(self, invalid_header_key: str, invalid_char):
        data = f'GET / HTTP/1.1\r\n{invalid_header_key}: Header Value'

        with pytest.raises(
                InvalidHTTPHeaderKey,
                match=re.escape(f"invalid HTTP header key {invalid_header_key!r}: character '{invalid_char}' is not accepted")
        ):
            parse_headers(data)

    @pytest.mark.parametrize(
        "request_headers, header_key, num_values",
        [
            ("Content-Type: Test Server\r\nContent-Type: text/html", "content-type", 2),
            ("Content-Length: 0\r\ncontent-length: 0", "content-length", 2),
            ("Host: Host 1\r\nhost: Host 2\r\nHOST: Host3", "host", 3),
            ("AUTHORIZATION: BearerXYZ\r\nAuthorization: BearerZYX", "authorization", 2),
            ("Content-Encoding: gzip, compressed,deflate", "content-encoding", 3),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_parse_disallowed_duplicate_request_headers(self, request_headers: str, header_key: str, num_values: int):
        data = f'GET / HTTP/1.1\r\n{request_headers}'

        with assert_raises(DuplicateHTTPHeader):
            parse_headers(data)

    @pytest.mark.parametrize(
        "invalid_request_headers",
        [
            "Server- Test",
            "Server Test Server",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_parse_invalid_request_headers(self, invalid_request_headers: str):
        data = f'GET / HTTP/1.1\r\n{invalid_request_headers}'

        with assert_raises(InvalidHTTPHeaders):
            parse_headers(data)


class TestRequestBodyParsing:
    @pytest.mark.parametrize(
        "request_method",
        [
            HTTPRequestMethod.POST,
            HTTPRequestMethod.PUT,
            HTTPRequestMethod.PATCH,
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_without_transfer_encoding_or_content_length(self, caplog, request_method: HTTPRequestMethod):
        fake_connection = FakeSocket([])

        request = HTTPRequest(
            method=request_method,
            url="/",
            protocol=HTTPProtocol.HTTP_1_1,
            headers={},
        )

        with pytest.raises(UnspecifiedBodyLength, match=re.escape(f"expected either 'Transfer-Encoding' or 'Content-Length' for method {request_method.value!r}")):
            request.parse_body(client_connection=fake_connection, body_buffer=b"")

    @pytest.mark.parametrize(
        "content_length, invalid_body_encoding",
        [
            ("1", b"\xff"),
            ("1", b"\x80"),
            ("1", b"\xc3"),
            ("4", b"\xf0\x28\x8c\xbc"),
            ("3", b"\xff\xfe\xfa"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_body_encoding(self, caplog, content_length: str, invalid_body_encoding: bytes):
        fake_connection = FakeSocket([])

        request = HTTPRequest(
            method=HTTPRequestMethod.POST,
            url="/",
            protocol=HTTPProtocol.HTTP_1_1,
            headers={"content-length": [content_length]},
        )

        with pytest.raises(InvalidDecoding, match=re.escape("unable to decode request, make sure it is encoded with UTF-8")):
            request.parse_body(client_connection=fake_connection, body_buffer=invalid_body_encoding)


    class TestRequestBodyTransferEncodingParsing:
        @pytest.mark.parametrize(
            "method, url, protocol, headers, bytes_body, expected_body",
            [
                (HTTPRequestMethod.POST, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"0\r\n\r\n", None),
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"1\r\nA\r\n0\r\n\r\n", "A"),
                (HTTPRequestMethod.PUT, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"2\r\nAB\r\n0\r\n\r\n", "AB"),
            ],
        )
        @pytest.mark.asyncio
        async def test_should_parse_valid_request_body_with_transfer_encoding(
                self,
                method: HTTPRequestMethod,
                url: str,
                protocol: HTTPProtocol,
                headers: Dict[str, str | List[str]],
                bytes_body: bytes,
                expected_body: Optional[str],
        ):
            fake_connection = FakeSocket([])

            request = HTTPRequest(method, url, protocol, headers)
            request.parse_body(fake_connection, bytes_body)

            assert_equal(request.body, expected_body)

        @pytest.mark.parametrize(
            "unsupported_transfer_encoding",
            [
                ["more than", "one transfer-encoding", "chunked"],
                ["compress"],
                ["deflate"],
                ["gzip"],
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_unsupported_transfer_encoding(self, unsupported_transfer_encoding: List[str]):
            fake_connection = FakeSocket([])

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"transfer-encoding": unsupported_transfer_encoding},
            )

            transfer_encoding_string = ",".join(unsupported_transfer_encoding)
            with pytest.raises(
                    UnsupportedTransferEncoding,
                    match=re.escape(f"'Transfer-Encoding': {transfer_encoding_string!r} is not supported, only 'chunked'")
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=b"")

        @pytest.mark.parametrize(
            "invalid_transfer_encoding",
            [
                "something random",
                "",
                " ",
                "None",
                "0"
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_invalid_transfer_encoding(self, invalid_transfer_encoding: str):
            fake_connection = FakeSocket([])

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"transfer-encoding": [invalid_transfer_encoding]},
            )

            transfer_encoding_string = f": {invalid_transfer_encoding!r}" if invalid_transfer_encoding else ""
            with pytest.raises(
                    InvalidTransferEncoding,
                    match=re.escape(f"'Transfer-Encoding'{transfer_encoding_string} is not valid")
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=b"")


    class TestRequestBodyContentLengthParsing:
        @pytest.mark.parametrize(
            "method, url, protocol, headers, bytes_body, expected_body",
            [
                (HTTPRequestMethod.GET, "/", HTTPProtocol.HTTP_1_1, {}, b"", None),
                (HTTPRequestMethod.POST, "/", HTTPProtocol.HTTP_1_1, {"content-length": ["0"]}, b"", None),
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"content-length": ["20"]}, b"Correct body length.", "Correct body length."),
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"content-length": ["8"]}, b"Big body to be cut.", "Big body"),
            ],
        )
        @pytest.mark.asyncio
        async def test_should_parse_valid_request_body_with_content_length(
                self,
                method: HTTPRequestMethod,
                url: str,
                protocol: HTTPProtocol,
                headers: Dict[str, str | List[str]],
                bytes_body: bytes,
                expected_body: Optional[str],
        ):
            fake_connection = FakeSocket([])

            request = HTTPRequest(method, url, protocol, headers)
            request.parse_body(fake_connection, bytes_body)

            assert_equal(request.body, expected_body)

        @pytest.mark.parametrize(
            "invalid_content_length",
            [
                "ABC",
                -1,
                "",
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_invalid_content_length(self, caplog, invalid_content_length: Any):
            fake_connection = FakeSocket([])

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"content-length": [invalid_content_length]},
            )

            content_length_string = f": {invalid_content_length!r}" if invalid_content_length else ""
            with pytest.raises(
                    InvalidContentLength,
                    match=re.escape(f"'Content-Length'{content_length_string} is not an integer greater or equal to zero")
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=b"")

        @pytest.mark.parametrize(
            "large_content_length",
            [
                9999999,
                1048577,
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_too_large_content_length(self, caplog, large_content_length: int):
            fake_connection = FakeSocket([])

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"content-length": [large_content_length]},
            )

            with pytest.raises(
                    BodyTooLarge,
                    match=re.escape(f"expected a body size smaller than {request.MAX_BODY_SIZE!r} bytes, got {large_content_length!r} bytes")
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=b"")

        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_invalid_body_length(self):
            fake_connection = FakeSocket([])

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"content-length": ["20"]},
            )

            with pytest.raises(InvalidBodyLength, match=re.escape("expected body with length 20, got 19 bytes")):
                request.parse_body(client_connection=fake_connection, body_buffer=b"Shorter than twenty")
