import pytest
from asserts import assert_equal, assert_raises

from request.exceptions import InvalidHTTPMethod, InvalidHTTPProtocol, InvalidHTTPHeaders
from request.http_request import HTTPRequest, parse_headers
from request.schema import HTTPRequestMethod
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
            ("", f"invalid HTTP method: expected [{EXPECTED_METHODS}], got '')"),
            (" ", f"invalid HTTP method: expected [{EXPECTED_METHODS}], got ' ')"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_parse_request_with_invalid_method(self, invalid_request_method, error_message: str):
        data = f"{invalid_request_method} / HTTP/1.1"

        with assert_raises(InvalidHTTPMethod, error_message):
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
            ("", f"invalid HTTP protocol: expected [{EXPECTED_PROTOCOL}], got '')"),
            (" ", f"invalid HTTP protocol: expected [{EXPECTED_PROTOCOL}], got ' ')"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_parse_request_with_invalid_protocol(self, invalid_request_protocol, error_message: str):
        data = f"GET / {invalid_request_protocol}"

        with assert_raises(InvalidHTTPProtocol, error_message):
            parse_headers(data)


class TestRequestHeadersParsing:
    @pytest.mark.parametrize(
        "request_headers, expected_headers",
        [
            ("", {}),
            ("Server: Test Server", {"Server": "Test Server"}),
            ("Server: Test Server\r\nContent-Type: text/html", {"Server": "Test Server", "Content-Type": "text/html"}),
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
