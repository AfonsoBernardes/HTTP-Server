import pytest
from asserts import assert_equal

from requests.request import Request
from requests.schema import RequestMethod, RequestProtocol


@pytest.mark.parametrize(
    "request_method",
    [
        request_method.value for request_method in RequestMethod
    ],
)
@pytest.mark.asyncio
async def test_should_parse_request_with_method(request_method: str):


    raw_data = f"{request_method} / HTTP/1.1\r\n\r\n".encode("utf-8")
    request = Request(raw_data)

    assert_equal(request.method, request_method)
    assert_equal(request.target, "/")
    assert_equal(request.protocol, RequestProtocol.HTTP_1_1)
    assert_equal(request.headers, {})
    assert_equal(request.body, None)
