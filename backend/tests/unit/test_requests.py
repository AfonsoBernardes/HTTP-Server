import pytest
from asserts import assert_equal, assert_raises

from requests.exceptions import InvalidHTTPMethod
from requests.request import Request
from requests.schema import RequestMethod, RequestProtocol


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

        assert_equal(request.method, request_method)
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
