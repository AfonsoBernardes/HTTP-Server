from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import patch

import pytest
from asserts import assert_equal, assert_in, assert_raises

from api.schema import ContentType
from conftest import FakeSocket
from response.exceptions import InvalidResponseHeader
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

class TestResponseHeaders:
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

    @pytest.mark.parametrize(
        "extra_headers",
        [
            "String",
            1,
            True,
        ],
    )
    @pytest.mark.asyncio
    async def test_should_fail_to_set_invalid_headers(self, extra_headers: Optional[Dict[str, str]]):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection, HTTPProtocol.HTTP_1_1)

        assert_equal(response.client_connection, fake_connection)
        assert_equal(response.protocol, HTTPProtocol.HTTP_1_1)
        assert_in("Server", response.headers)

        with assert_raises(InvalidResponseHeader, "invalid response header"):
            response.set_headers(extra_headers)

    @patch("response.http_response.datetime")
    @pytest.mark.parametrize(
        "extra_headers, expected_headers_string",
        [
            (None, "Server: Afonso's Server\r\nDate: 2026-01-01T00:00:00+00:00\r\n"),
            ({}, "Server: Afonso's Server\r\nDate: 2026-01-01T00:00:00+00:00\r\n"),
            ({"Key": "Value"}, "Server: Afonso's Server\r\nDate: 2026-01-01T00:00:00+00:00\r\nKey: Value\r\n"),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_get_headers(self, mock_datetime: datetime, extra_headers: Optional[Dict[str, str]], expected_headers_string: str):
        mock_datetime.now.return_value = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection, HTTPProtocol.HTTP_1_1)
        response.set_headers(extra_headers)

        assert_equal(response.client_connection, fake_connection)
        assert_equal(response.protocol, HTTPProtocol.HTTP_1_1)
        assert_in("Server", response.headers)
        assert_in("Date", response.headers)

        headers_string = response.get_headers()
        assert_equal(headers_string, expected_headers_string)


class TestResponseBody:
    TEST_FILE_PATH = Path("./tests")

    # HTML
    TEST_HTML = open(TEST_FILE_PATH / "test.html", 'r', encoding='utf-8').read()
    EXPECTED_HTML_STRING = '<!DOCTYPE html>\n<html lang="en">\n    <head>\n        <meta charset="UTF-8">\n        <title>Afonso\'s Server</title>\n    </head>\n    <body>\n        <h1>Test File</h1>\n        <div>\n            <p>This is a test paragraph</p>\n        </div>\n    </body>\n</html>'

    # CSS
    TEST_CSS = open(TEST_FILE_PATH / "test.css", 'r', encoding='utf-8').read()
    EXPECTED_CSS_STRING = "body {\n    background-color: powderblue;\n}\n\nh1 {\n    color: goldenrod;\n    margin-left: 20px;\n}"

    @pytest.mark.parametrize(
        "body, content_type, expected_body_string",
        [
            (None, ContentType.JSON, "null"),
            ({}, ContentType.JSON, "{}"),
            ({"Key": "Value"}, ContentType.JSON, '{"Key": "Value"}'),
            ("", ContentType.PLAIN, ""),
            ("plain text", ContentType.PLAIN, "plain text"),
            ("", ContentType.HTML, ""),
            (TEST_HTML, ContentType.HTML, EXPECTED_HTML_STRING),
            ("", ContentType.CSS, ""),
            (TEST_CSS, ContentType.CSS, EXPECTED_CSS_STRING),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_transform_body(self, body, content_type: ContentType, expected_body_string: str):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection, HTTPProtocol.HTTP_1_1)

        assert_equal(response.client_connection, fake_connection)
        assert_equal(response.protocol, HTTPProtocol.HTTP_1_1)
        assert_in("Server", response.headers)

        body_string = response._transform_body(body=body, content_type=content_type)
        assert_equal(body_string, expected_body_string)
