from typing import List

from displayable_exceptions.http_exception import HTTPServerException
from request.schema import HTTPRequestMethod
from response.schema import HTTPResponseStatusCode
from server.schema import HTTPProtocol


class InvalidHTTPMethod(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    EXPECTED_METHODS = [method.value for method in HTTPRequestMethod]

    def __init__(self, method: str):
        super().__init__(f"invalid HTTP method: expected [{", ".join(self.EXPECTED_METHODS)}], got {method!r}")


class InvalidHTTPProtocol(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    EXPECTED_PROTOCOLS = [protocol.value for protocol in HTTPProtocol]

    def __init__(self, protocol: str):
        super().__init__(f"invalid HTTP protocol: expected [{", ".join(self.EXPECTED_PROTOCOLS)}], got {protocol!r}")


class InvalidHTTPHeaders(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self):
        super().__init__(
            f"invalid HTTP headers: make sure headers are key-value pairs, separated by ': ' and a line breaker"
        )


class DuplicateHTTPHeader(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, header_key: str, num_values: int):
        super().__init__(f"duplicate HTTP header: expected one value for {header_key!r}, got {num_values!r}]")
