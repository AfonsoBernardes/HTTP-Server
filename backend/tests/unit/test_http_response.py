from typing import Dict, Optional

import pytest
from asserts import assert_equal, assert_in

from conftest import FakeSocket
from response.http_response import HTTPResponse
from response.schema import HTTPResponseStatusCode
from server.schema import HTTPProtocol


class TestResponse:
    @pytest.mark.parametrize(
        "http_protocol",
        [
            protocol for protocol in HTTPProtocol
        ],
    )
    @pytest.mark.asyncio
    async def test_should_create_response(self, http_protocol: HTTPProtocol):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection, http_protocol)

        assert_equal(response.client_connection, fake_connection)
        assert_equal(response.protocol, http_protocol)
        assert_equal(response.headers, {"Server": "Afonso's Server"})

    @pytest.mark.parametrize(
        "status_code",
        [
            status_code for status_code in HTTPResponseStatusCode
        ],
    )
    @pytest.mark.asyncio
    async def test_should_set_status_code(self, status_code: HTTPResponseStatusCode):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection, HTTPProtocol.HTTP_1_1)
        response.set_status_code(status_code)

        assert_equal(response.client_connection, fake_connection)
        assert_equal(response.protocol, HTTPProtocol.HTTP_1_1)
        assert_equal(response.headers, {"Server": "Afonso's Server"})
        assert_equal(response.status_code, status_code)

    @pytest.mark.parametrize(
        "extra_headers",
        [
            None,
            {},
            {"Key": "Value"},
        ],
    )
    @pytest.mark.asyncio
    async def test_should_set_headers(self, extra_headers: Optional[Dict[str, str]]):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection, HTTPProtocol.HTTP_1_1)
        response.set_headers(extra_headers)

        assert_equal(response.client_connection, fake_connection)
        assert_equal(response.protocol, HTTPProtocol.HTTP_1_1)
        assert_in("Server", response.headers)
        assert_in("Date", response.headers)

        if extra_headers:
            for header_key in extra_headers.keys():
                assert_in(header_key, response.headers)
                assert_equal(extra_headers[header_key], response.headers[header_key])

