import pytest
from asserts import assert_equal

from response.http_response import HTTPResponse
from server.schema import HTTPProtocol


class FakeSocket:
    def __init__(self, chunks):
        self._chunks = iter(chunks)

    def recv(self, bufsize: int):
        return next(self._chunks, b"")

    def send(self, data: bytes):
        pass



class TestServerHeaderHandling:
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
