import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import patch

import pytest
from asserts import assert_equal, assert_in

from api.schema import ContentType
from conftest import FakeSocket
from response.exceptions import InvalidResponseHeader, InvalidBody
from response.http_response import HTTPResponse
from response.schema import HTTPResponseStatusCode
from server.schema import HTTPProtocol


class TestResponse:
    @pytest.mark.asyncio
    async def test_should_create_response(self):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection)

        assert_equal(response.client_connection, fake_connection)
        assert_equal(response.headers, {"Server": "Afonso's Server"})

    @pytest.mark.parametrize(
        "http_protocol",
        [
            protocol for protocol in HTTPProtocol
        ],
    )
    @pytest.mark.asyncio
    async def test_should_set_protocol(self, http_protocol: HTTPProtocol):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection)
        response.set_protocol(http_protocol)

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

        response = HTTPResponse(fake_connection)
        response.set_status_code(status_code)

        assert_equal(response.client_connection, fake_connection)
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

        response = HTTPResponse(fake_connection)
        response.set_headers(extra_headers)

        assert_equal(response.client_connection, fake_connection)
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

        response = HTTPResponse(fake_connection)

        assert_equal(response.client_connection, fake_connection)
        assert_in("Server", response.headers)

        with pytest.raises(InvalidResponseHeader, match=re.escape("invalid response header")):
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

        response = HTTPResponse(fake_connection)
        response.set_headers(extra_headers)

        assert_equal(response.client_connection, fake_connection)
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

    # JS
    TEST_JS = open(TEST_FILE_PATH / "test.js", 'r', encoding='utf-8').read()
    EXPECTED_JS_STRING = "console.log('Test JS file.');"

    # CSV
    TEST_CSV = open(TEST_FILE_PATH / "test.csv", 'r', encoding='utf-8').read()
    EXPECTED_CSV_STRING = 'COL_1,COL_2,COL_3\n2026-01-01T00:00:00+00,1,"A"\n2026-01-01T00:00:00+00,2,"B"'

    @pytest.mark.parametrize(
        "body, content_type, expected_body_string",
        [
            (None, ContentType.JSON, "null"),
            ({}, ContentType.JSON, "{}"),
            ({"Key": "Value"}, ContentType.JSON, '{"Key": "Value"}'),
            (None, ContentType.PLAIN, ""),
            ("", ContentType.PLAIN, ""),
            ("plain text", ContentType.PLAIN, "plain text"),
            (None, ContentType.HTML, ""),
            ("", ContentType.HTML, ""),
            (TEST_HTML, ContentType.HTML, EXPECTED_HTML_STRING),
            (None, ContentType.CSS, ""),
            ("", ContentType.CSS, ""),
            (TEST_CSS, ContentType.CSS, EXPECTED_CSS_STRING),
            (None, ContentType.JAVASCRIPT, ""),
            ("", ContentType.JAVASCRIPT, ""),
            (TEST_JS, ContentType.JAVASCRIPT, EXPECTED_JS_STRING),
            (None, ContentType.CSV, ""),
            ("", ContentType.CSV, ""),
            (TEST_CSV, ContentType.CSV, EXPECTED_CSV_STRING),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_transform_body(self, body, content_type: ContentType, expected_body_string: str):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection)

        assert_equal(response.client_connection, fake_connection)
        assert_in("Server", response.headers)

        body_string = response._transform_body(body=body, content_type=content_type)
        assert_equal(body_string, expected_body_string)

    @pytest.mark.parametrize(
        "body, content_type, expected_body_string",
        [
            (None, ContentType.JSON, "null"),
            ({}, ContentType.JSON, "{}"),
            ({"Key": "Value"}, ContentType.JSON, '{"Key": "Value"}'),
            (None, ContentType.PLAIN, ""),
            ("", ContentType.PLAIN, ""),
            ("plain text", ContentType.PLAIN, "plain text"),
            (None, ContentType.HTML, ""),
            ("", ContentType.HTML, ""),
            (TEST_HTML, ContentType.HTML, EXPECTED_HTML_STRING),
            (None, ContentType.CSS, ""),
            ("", ContentType.CSS, ""),
            (TEST_CSS, ContentType.CSS, EXPECTED_CSS_STRING),
            (None, ContentType.JAVASCRIPT, ""),
            ("", ContentType.JAVASCRIPT, ""),
            (TEST_JS, ContentType.JAVASCRIPT, EXPECTED_JS_STRING),
            (None, ContentType.CSV, ""),
            ("", ContentType.CSV, ""),
            (TEST_CSV, ContentType.CSV, EXPECTED_CSV_STRING),
        ],
    )
    @pytest.mark.asyncio
    async def test_should_set_body(self, body, content_type: ContentType, expected_body_string: str):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection)

        assert_equal(response.client_connection, fake_connection)
        assert_in("Server", response.headers)

        response.set_body(body=body, content_type=content_type)
        assert_equal(response.body, expected_body_string)
        assert_equal(response.headers["Content-Type"], content_type.value)

    @pytest.mark.asyncio
    async def test_should_get_body(self):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection)

        assert_equal(response.client_connection, fake_connection)
        assert_in("Server", response.headers)

        response.set_body(body="Test body", content_type=ContentType.PLAIN)
        body = response.get_body()
        assert_equal(body, "Test body")

    @pytest.mark.parametrize(
        "body, content_type",
        [
            ({"A", "B"}, ContentType.JSON),
            (datetime(year=2020, month=1, day=1, hour=0, minute=0, second=0), ContentType.JSON),
            (b"invalid", ContentType.JSON),
            (Decimal("1.2"), ContentType.JSON),
        ],
    )
    @pytest.mark.asyncio
    async def test_fail_to_set_body_with_wrong_content_type(self, body, content_type: ContentType):
        fake_connection = FakeSocket([])

        response = HTTPResponse(fake_connection)

        assert_equal(response.client_connection, fake_connection)
        assert_in("Server", response.headers)

        with pytest.raises(InvalidBody, match=re.escape(f"body '{body}' cannot be serialized as '{content_type.value}'")):
            response.set_body(body=body, content_type=content_type)
