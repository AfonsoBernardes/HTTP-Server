from typing import Any, Optional

from displayable_exceptions.http_exception import HTTPServerException
from response.schema import HTTPResponseStatusCode


class InvalidDecoding(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self):
        super().__init__("unable to decode request")


class InvalidRequest(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self):
        super().__init__("invalid request; make sure the request follows HTTP/1.X standards")


class InvalidBodyLength(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, body_length: int, expected_length: int):
        super().__init__(f"expected body with length {expected_length}, got {body_length} bytes")


class InvalidContentLength(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, content_length: Optional[Any]):
        content_length_string = f": {content_length!r}" if content_length is not None else ""
        super().__init__(f"'Content-Length'{content_length_string} is not a valid positive integer")
