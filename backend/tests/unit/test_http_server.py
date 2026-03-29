import pytest
from asserts import assert_raises

from server.exceptions import InvalidDecoding, InvalidRequest, InvalidBodyLength
from server.http_server import HTTPServer

class FakeSocket:
    def __init__(self, chunks):
        self._chunks = iter(chunks)

    def recv(self, bufsize: int):
        return next(self._chunks, b"")

    def send(self, data: bytes):
        pass



class TestServerHeaderHandling:
    @pytest.mark.asyncio
    async def test_should_handle_valid_request(self):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            b"GET / HTTP/1.1\r\n\r\n"
        ])

        assert http_server.handle_request(fake_connection)

    @pytest.mark.parametrize(
        "invalid_headers",
        [
            b"GET / HTTP/1.1",
            b"GET / HTTP/1.1\r\n",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_without_two_line_breaks(self, invalid_headers: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_headers,
            b"",
        ])

        with assert_raises(InvalidRequest):
            http_server.handle_request(fake_connection)

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
    async def test_should_fail_to_handle_request_with_invalid_header_encoding(self, invalid_header_encoding: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_header_encoding,
        ])

        with assert_raises(InvalidDecoding):
            http_server.handle_request(fake_connection)

class TestServerBodyHandling:
    @pytest.mark.parametrize(
        "byte_request",
        [
            b"GET / HTTP/1.1\r\nContent-Length: 0\r\n\r\n",
            b"GET / HTTP/1.1\r\nContent-Length: 20\r\n\r\nCorrect body length.",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_handle_request_with_valid_body(self, byte_request: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            byte_request,
        ])

        assert http_server.handle_request(fake_connection)

    @pytest.mark.parametrize(
        "invalid_body",
        [
            b"GET / HTTP/1.1\r\nContent-Length: 0\r\n\r\nGreater than zero",
            b"GET / HTTP/1.1\r\nContent-Length: 20\r\n\r\nShorter than twenty",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_body(self, invalid_body: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_body,
        ])

        with assert_raises(InvalidBodyLength):
            http_server.handle_request(fake_connection)

    @pytest.mark.parametrize(
        "invalid_body_encoding",
        [
            b"GET / HTTP/1.1\r\nContent-Length: 1\r\n\r\n\xff",
            b"GET / HTTP/1.1\r\nContent-Length: 1\r\n\r\n\x80",
            b"GET / HTTP/1.1\r\nContent-Length: 1\r\n\r\n\xc3",
            b"GET / HTTP/1.1\r\nContent-Length: 4\r\n\r\n\xf0\x28\x8c\xbc",
            b"GET / HTTP/1.1\r\nContent-Length: 3\r\n\r\n\xff\xfe\xfa",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_handle_request_with_invalid_body_encoding(self, invalid_body_encoding: bytes):
        http_server = HTTPServer()
        fake_connection = FakeSocket([
            invalid_body_encoding,
        ])

        with assert_raises(InvalidDecoding):
            http_server.handle_request(fake_connection)

