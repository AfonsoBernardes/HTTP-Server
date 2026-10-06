import re
from typing import Optional, Dict, List, Any

import pytest
from asserts import assert_equal, assert_raises

from conftest import FakeSocket
from request.exceptions import (
    AmbiguousBodyLength,
    InvalidRequestLine,
    InvalidHTTPMethod,
    InvalidHTTPProtocol,
    InvalidHTTPHeaders,
    DuplicateHTTPHeader,
    InvalidBodyLength,
    InvalidContentLength,
    BodyTooLarge,
    UnspecifiedBodyLength,
    UnsupportedTransferEncoding,
    IncompleteChunkedBody,
    InvalidChunkDelimiter,
    InvalidTransferEncoding,
    InvalidHTTPHeaderKey,
    InvalidChunkSize,
    ChunkSizeTooLarge, ChunkLineTooLarge, TrailerSectionTooLarge,
)
from request.http_request import HTTPRequest, parse_headers
from request.schema import HTTPRequestMethod
from server.config import DEFAULT_LIMITS, ServerLimits
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
    async def test_should_fail_to_parse_request_with_invalid_method(self, invalid_request_method: str, error_message: str):
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
        "request_line, error_message",
        [
            ("GET / ", f"invalid HTTP protocol: expected [{EXPECTED_PROTOCOL}], got None"),
            ("GET  / HTTP/1.1", f"invalid HTTP protocol: expected [{EXPECTED_PROTOCOL}], got '/ HTTP/1.1'"),
            ("GET / HTTP/1.1 SMTH", f"invalid HTTP protocol: expected [{EXPECTED_PROTOCOL}], got 'HTTP/1.1 SMTH'"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_parse_request_with_invalid_protocol(self, request_line: str, error_message: str):
        with pytest.raises(InvalidHTTPProtocol, match=re.escape(error_message)):
            parse_headers(request_line)


class TestRequestHeadersParsing:
    def test_should_parse_headers_with_valid_request_line(self):
        method, url, protocol, headers = parse_headers("GET /path HTTP/1.1\r\nHost: localhost:8000")

        assert method == HTTPRequestMethod.GET
        assert url == "/path"
        assert protocol == HTTPProtocol.HTTP_1_1
        assert headers == {"host": ["localhost:8000"]}

    @pytest.mark.parametrize(
        "request_headers, expected_headers",
        [
            ("Header-Key: Header Value", {"header-key": ["Header Value"]}),
            ("Header-Key:Header Value", {"header-key": ["Header Value"]}),
            ("Header-Key: Header:Value", {"header-key": ["Header:Value"]}),
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
        "request_headers, expected_headers",
        [
            ("User-Agent: Mozilla/5.0 (KHTML, like Gecko)", {"user-agent": ["Mozilla/5.0 (KHTML, like Gecko)"]}),  # not a list: comma kept
            ("Date: Tue, 29 Sep 2026 10:00:00 GMT", {"date": ["Tue, 29 Sep 2026 10:00:00 GMT"]}),  # not a list: comma and colons kept
            ('Authorization: Digest username="a", realm="b"', {"authorization": ['Digest username="a", realm="b"']}) , # single value: comma kept
            ("Accept: text/html\r\naccept: application/json, text/plain", {"accept": ["text/html", "application/json", "text/plain"]}),  # list header, repeated line
            ("Transfer-Encoding: gzip, chunked", {"transfer-encoding": ["gzip", "chunked"]}),  # list header, split
            ("Unknown-Header: single, line", {"unknown-header": ["single, line"]}),  # unknown header, single line
            ("Unknown-Header: repeated\r\nUnknown-Header: line", {"unknown-header": ["repeated", "line"]}),  # unknown header, repeated line
        ],
    )
    @pytest.mark.asyncio
    async def test_should_parse_header_values_by_type(self, request_headers: str, expected_headers: dict):
        data = f'GET / HTTP/1.1\r\n{request_headers}'

        method, url, protocol, headers = parse_headers(data)
        request = HTTPRequest(method, url, protocol, headers)

        assert_equal(request.method, HTTPRequestMethod.GET)
        assert_equal(request.url, "/")
        assert_equal(request.protocol, HTTPProtocol.HTTP_1_1)
        assert_equal(request.headers, expected_headers)

    @pytest.mark.parametrize(
        "invalid_request_line",
        [
            "",
            "GET",
            "GET /",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_parse_request_with_invalid_request_line(self, invalid_request_line: str):
        with pytest.raises(
                InvalidRequestLine,
                match=re.escape(f"invalid request line: expected '<METHOD> <TARGET> <PROTOCOL>', got {invalid_request_line!r}")
        ):
            parse_headers(invalid_request_line)

    @pytest.mark.parametrize(
        "invalid_header_key, invalid_char",
        [
            ("Header Key", " "),
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
    async def test_should_fail_to_handle_request_without_transfer_encoding_or_content_length(self, request_method: HTTPRequestMethod):
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
    async def test_should_fail_to_handle_request_with_invalid_body_encoding(self, content_length: str, invalid_body_encoding: bytes):
        fake_connection = FakeSocket([])

        request = HTTPRequest(
            method=HTTPRequestMethod.POST,
            url="/",
            protocol=HTTPProtocol.HTTP_1_1,
            headers={"content-length": [content_length]},
        )

        with pytest.raises(InvalidDecoding, match=re.escape("unable to decode request, make sure it is encoded with UTF-8")):
            request.parse_body(client_connection=fake_connection, body_buffer=invalid_body_encoding)

    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_too_large_body(self):
        fake_connection = FakeSocket([])
        test_limits = ServerLimits(max_body_size=2)

        request = HTTPRequest(
            method=HTTPRequestMethod.POST,
            url="/",
            protocol=HTTPProtocol.HTTP_1_1,
            headers={"transfer-encoding": ["chunked"]},
        )

        body_buffer = b"1\r\nA\r\n1\r\nB\r\n1\r\nC\r\n0\r\n\r\n"
        with pytest.raises(
                BodyTooLarge,
                match=re.escape(f"expected a body size smaller than {test_limits.max_body_size!r} bytes, got 3 bytes")
        ):
            request.parse_body(client_connection=fake_connection, body_buffer=body_buffer, limits=test_limits)

    @pytest.mark.parametrize(
        "headers",
        [
            {"transfer-encoding": ["chunked"], "content-length": ["5"]},
            {"transfer-encoding": ["gzip"], "content-length": ["5"]},  # conflict is reported before the encoding is validated
            {"transfer-encoding": ["chunked"], "content-length": [""]},  # present but empty still counts
        ],
    )
    def test_should_fail_to_handle_request_with_both_transfer_encoding_and_content_length(self, headers: dict):
        fake_connection = FakeSocket([])
        request = HTTPRequest(
            method=HTTPRequestMethod.POST,
            url="/",
            protocol=HTTPProtocol.HTTP_1_1,
            headers=headers,
        )

        with pytest.raises(
                AmbiguousBodyLength,
                match=re.escape("expected only one of 'Transfer-Encoding' or 'Content-Length', got both"),
        ):
            request.parse_body(client_connection=fake_connection, body_buffer=b"")


    class TestRequestBodyTransferEncodingParsing:
        @pytest.mark.parametrize(
            "method, url, protocol, headers, bytes_body, expected_body",
            [
                (HTTPRequestMethod.POST, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"0\r\n\r\n", None),
                (HTTPRequestMethod.POST, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"0\r\n\r\nGET", None),  # contains start of next request
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"1\r\nA\r\n0\r\n\r\n", "A"),
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"001\r\nA\r\n0\r\n\r\n", "A"),  # leading zeros
                (HTTPRequestMethod.PUT, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"2\r\nAB\r\n0\r\n\r\n", "AB"),
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"2\r\nAB\r\n1\r\nC\r\n0\r\n\r\n", "ABC"),
                (HTTPRequestMethod.PUT, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"B\r\nABCDEFGHIJK\r\n0\r\n\r\n", "ABCDEFGHIJK"),
                (HTTPRequestMethod.PUT, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"b\r\nABCDEFGHIJK\r\n0\r\n\r\n", "ABCDEFGHIJK"),  # upper and lower case should be the same
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"A\r\nABCDEFGHIJ\r\n1\r\nK\r\n0\r\n\r\n", "ABCDEFGHIJK"),
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"1;extension=something\r\nA\r\n0\r\n\r\n", "A"),  # ignore extensions
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"1\r\nA\r\n0\r\nExpires: Date\r\nX-Checksum: something\r\n\r\n", "A"),  # ignore trailer-fields
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"transfer-encoding": ["chunked"]}, b"1;extension=something\r\nA\r\n0\r\nExpires: Date\r\n\r\nGET", "A"),  # contains start of next request
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

        @pytest.mark.parametrize(
            "body_buffer, socket_chunks",
            [
                (b"5", []),  # chunk-size line never finishes
                (b"5\r\nabc", []),  # chunk data cut short (3 of 5 bytes)
                (b"3\r\nabc", []),  # delimiter after chunk data missing
                (b"0\r\n", []),  # zero-size chunk, no final blank line
                (b"0\r\nX-Trailer: a\r\n", []),  # trailer present, no final blank line
                (b"", [b"3\r\nab"]),  # data arrives via recv(), then disconnect
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_incomplete_chunked_body(self, body_buffer: bytes, socket_chunks: List[bytes]):
            fake_connection = FakeSocket(socket_chunks)

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"transfer-encoding": ["chunked"]},
            )

            with pytest.raises(
                    IncompleteChunkedBody,
                    match=re.escape(f'client connection {fake_connection!r} closed before the full chunked body was received')
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=body_buffer)

        @pytest.mark.parametrize(
            "body_buffer, socket_chunks, chunk_line_size",
            [
                (b"AAAAAAA", [], 7),  # no CRLF, body buffer too long
                (b"", [b"AAAAAAA"], 7),  # no CRLF, chunk too long
                (b"AAAA", [b"AAA"], 7),  # no CRLF, body buffer + chunk too long
                (b"AAAAAA\r\n", [], 6),  # CRLF present line too long
                (b"A", [b"AA", b"AAA\r\n"], 6),
                (b"", [b"AAA", b"AAA\r\n"], 6),
                (b"3;XXXX\r\n", [], 6),  # chunk extension too long
                (b"0\r\nX: AAA\r\n\r\n", [], 6),  # trailer line too lo g
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_chunk_line_too_large(self, body_buffer: bytes, socket_chunks: List[bytes], chunk_line_size: int):
            test_limits = ServerLimits(max_chunk_line_size=5)

            fake_connection = FakeSocket(socket_chunks)

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"transfer-encoding": ["chunked"]},
            )

            with pytest.raises(
                    ChunkLineTooLarge,
                    match=re.escape(f'expected a chunk line smaller than {test_limits.max_chunk_line_size!r} bytes, got {chunk_line_size!r} bytes')
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=body_buffer, limits=test_limits)

        @pytest.mark.parametrize(
            "invalid_chunk_size, invalid_chunk_size_string",
            [
                (b"", b''),
                (b";extension=no-size", b''),
                (b"g", b"g"),
                (b" 1", b" 1"),  # leading space
                (b"1 ", b"1 "),  #trailing space
                (b"-1", b"-1"),  # sign not allowed
                (b"+1", b"+1"),
                (b"1_a", b"1_a"),  # separator not allowed
                (b"0x1", b"0x1")  # prefix against chunk size grammar
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_invalid_chunk_size(self, invalid_chunk_size: bytes, invalid_chunk_size_string: str):
            fake_connection = FakeSocket([])

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"transfer-encoding": ["chunked"]},
            )

            body_buffer = invalid_chunk_size + b"\r\nA\r\n0\r\n\r\n"

            invalid_chunk_size_string = f'"{invalid_chunk_size_string}"' if invalid_chunk_size_string else ''
            with pytest.raises(
                    InvalidChunkSize,
                    match=re.escape(f'chunk size must be a non-negative integer in hexadecimal format, got {invalid_chunk_size_string}')
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=body_buffer)

        @pytest.mark.parametrize(
            "large_chunk_size",
            [
                b"98967F",
                b"500001",
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_too_large_chunk_size(self, large_chunk_size: bytes):
            fake_connection = FakeSocket([])
            test_limits = ServerLimits(max_chunk_size=1)

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"transfer-encoding": ["chunked"]},
            )

            body_buffer = large_chunk_size + b"\r\nA\r\n0\r\n\r\n"
            chunk_size = int(large_chunk_size.decode("ascii"), 16)
            with pytest.raises(
                    ChunkSizeTooLarge,
                    match=re.escape(f"expected a chunk size smaller than {test_limits.max_chunk_size!r} bytes, got {chunk_size!r} bytes")
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=body_buffer, limits=test_limits)

        @pytest.mark.parametrize(
            "body_buffer, socket_chunks, trailer_size",
            [
                (b"3\r\nABC\r\n0\r\nX: A\r\nX: B\r\n", [], 6),
                (b"3\r\nABC\r\n0\r\nX: A\r\n", [b"X: B\r\n"], 6),
                (b"3\r\nABC\r\n0\r", [b"\nX: A\r\nX: B\r\n"], 6),
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_trailer_section_too_large(self, body_buffer: bytes, socket_chunks: List[bytes], trailer_size: int):
            test_limits = ServerLimits(max_trailer_size=5)

            fake_connection = FakeSocket(socket_chunks)

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"transfer-encoding": ["chunked"]},
            )

            with pytest.raises(
                    TrailerSectionTooLarge,
                    match=re.escape(f'expected a trailer section smaller than {test_limits.max_trailer_size!r} bytes, got {trailer_size!r} bytes')
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=body_buffer, limits=test_limits)

        @pytest.mark.parametrize(
            "body_buffer, socket_chunks, delimiter",
            [
                (b"3\r\nabcXX0\r\n\r\n", [], b"XX"),  # arbitrary bytes instead of CRLF
                (b"3\r\nabcd\r\n0\r\n\r\n", [], b"d\r"),  # client sent more data than the declared size
                (b"3\r\nabc\n\r0\r\n\r\n", [], b"\n\r"),  # CR and LF swapped
                (b"3\r\nabc\r\r0\r\n\r\n", [], b"\r\r"),  # CR without LF
                (b"3\r\nabc  0\r\n\r\n", [], b"  "),  # spaces instead of CRLF
                (b"3\r\nabc", [b"XX0\r\n\r\n"], b"XX"),  # delimiter arrives entirely via recv()
                (b"3\r\nabc\r", [b"X0\r\n\r\n"], b"\rX"),  # delimiter split across buffer and recv()
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_invalid_chunk_delimiter(self, body_buffer: bytes, socket_chunks: List[bytes], delimiter: bytes):
            fake_connection = FakeSocket(socket_chunks)

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"transfer-encoding": ["chunked"]},
            )

            with pytest.raises(
                    InvalidChunkDelimiter,
                    match=re.escape(f"chunk data must be followed by '\\r\\n', got {delimiter!r}")
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=body_buffer)


    class TestRequestBodyContentLengthParsing:
        @pytest.mark.parametrize(
            "method, url, protocol, headers, bytes_body, expected_body",
            [
                (HTTPRequestMethod.GET, "/", HTTPProtocol.HTTP_1_1, {}, b"", None),
                (HTTPRequestMethod.POST, "/", HTTPProtocol.HTTP_1_1, {"content-length": ["0"]}, b"", None),
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"content-length": ["20"]}, b"Correct body length.", "Correct body length."),
                (HTTPRequestMethod.PATCH, "/", HTTPProtocol.HTTP_1_1, {"content-length": ["08"]}, b"Big body to be cut.", "Big body"),
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
                "",
                "+5",
                "-5",
                "-0",
                "1_0",
                "0x5",
                "5.0",
                "5, 5",
                "one"
                "٥",  # Arabic-Indic digit, accepted by int()
                " 5",
                "5 ",
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_invalid_content_length(self, invalid_content_length: Any):
            fake_connection = FakeSocket([])

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"content-length": [invalid_content_length]},
            )

            content_length_string = f"{invalid_content_length!r}" if invalid_content_length else ""
            with pytest.raises(
                    InvalidContentLength,
                    match=re.escape(f"expected 'Content-Length' to be an integer greater or equal to zero, got {content_length_string}")
            ):
                request.parse_body(client_connection=fake_connection, body_buffer=b"")

        @pytest.mark.parametrize(
            "large_content_length",
            [
                "99999999",
                "10485761",
            ],
        )
        @pytest.mark.asyncio
        async def test_should_fail_to_handle_request_with_too_large_content_length(self, large_content_length: int):
            fake_connection = FakeSocket([])

            request = HTTPRequest(
                method=HTTPRequestMethod.POST,
                url="/",
                protocol=HTTPProtocol.HTTP_1_1,
                headers={"content-length": [large_content_length]},
            )

            with pytest.raises(
                    BodyTooLarge,
                    match=re.escape(f"expected a body size smaller than {DEFAULT_LIMITS.max_body_size!r} bytes, got {large_content_length} bytes")
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
