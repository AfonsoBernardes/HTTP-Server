import pytest
from asserts import assert_equal, assert_raises

from requests.exceptions import InvalidHTTPMethod, InvalidRequest, InvalidHTTPProtocol
from requests.request import Request
from requests.schema import RequestMethod, RequestProtocol


class TestRequestParsing:
    @pytest.mark.parametrize(
        "request_headers, expected_headers",
        [
            ("", {}),
            ("Server: Test Server", {"Server": "Test Server"}),
            ("Server: Test Server\r\nContent Type: text/html", {"Server": "Test Server", "Content Type": "text/html"}),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_parse_request_with_valid_headers(self, request_headers: str, expected_headers: dict):
        raw_data = f'GET / HTTP/1.1\r\n{request_headers}\r\n\r\n'.encode("utf-8")
        request = Request(raw_data)

        assert_equal(request.method, RequestMethod.GET)
        assert_equal(request.target, "/")
        assert_equal(request.protocol, RequestProtocol.HTTP_1_1)
        assert_equal(request.headers, expected_headers)

    @pytest.mark.parametrize(
        "invalid_byte_request",
        [
            b"GET / HTTP/1.1",
            b"GET / HTTP/1.1\r\n",
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_parse_request_without_two_linebreaks(self, invalid_byte_request):
        with assert_raises(InvalidRequest):
            Request(invalid_byte_request)

class TestRequestMethod:
    EXPECTED_METHODS = ", ".join(method.value for method in RequestMethod)

    @pytest.mark.parametrize(
        "request_method",
        [
            request_method.value for request_method in RequestMethod
        ],
    )
    @pytest.mark.asyncio
    async def test_should_parse_request_with_valid_method(self, request_method: str):
        raw_data = f"{request_method} / HTTP/1.1\r\n\r\n".encode("utf-8")
        request = Request(raw_data)

        assert_equal(request.method, RequestMethod(request_method))
        assert_equal(request.target, "/")
        assert_equal(request.protocol, RequestProtocol.HTTP_1_1)
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
        raw_data = f"{invalid_request_method} / HTTP/1.1\r\n\r\n".encode("utf-8")

        with assert_raises(InvalidHTTPMethod, error_message):
            Request(raw_data)



class TestRequestProtocol:
    EXPECTED_PROTOCOL = ", ".join(protocol.value for protocol in RequestProtocol)

    @pytest.mark.parametrize(
        "request_protocol",
        [
            request_protocol.value for request_protocol in RequestProtocol
        ],
    )
    @pytest.mark.asyncio
    async def test_should_parse_request_with_valid_protocol(self, request_protocol: str):
        raw_data = f"GET / {request_protocol}\r\n\r\n".encode("utf-8")
        request = Request(raw_data)

        assert_equal(request.method, "GET")
        assert_equal(request.target, "/")
        assert_equal(request.protocol, RequestProtocol(request_protocol))
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
        raw_data = f"GET / {invalid_request_protocol}\r\n\r\n".encode("utf-8")

        with assert_raises(InvalidHTTPProtocol, error_message):
            Request(raw_data)
