from typing import Any

from api.schema import ContentType
from displayable_exceptions.http_exception import HTTPServerException
from response.schema import HTTPResponseStatusCode


class InvalidHTTPStatusCode(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_500

    def __init__(self, status_code: int):
        super().__init__(f"invalid HTTP status code {status_code!r}")


class InvalidResponseHeader(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_500

    def __init__(self):
        super().__init__(f"invalid response header")


class InvalidContent(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_500

    def __init__(self):
        super().__init__(f"invalid response header")


class InvalidBody(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_500

    def __init__(self, body: Any, content_type: ContentType):
        super().__init__(f"body '{body}' cannot be serialized as {content_type.value!r}")
