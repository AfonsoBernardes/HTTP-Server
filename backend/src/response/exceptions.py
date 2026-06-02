from typing import Any

from api.schema import ContentType
from displayable_exceptions.displayable_exception import DisplayableException


class InvalidHTTPStatusCode(DisplayableException):
    def __init__(self, status_code: int):
        super().__init__(f"invalid HTTP status code {status_code!r}")


class InvalidResponseHeader(DisplayableException):
    def __init__(self):
        super().__init__(f"invalid response header")

class InvalidContent(DisplayableException):
    def __init__(self):
        super().__init__(f"invalid response header")

class InvalidBody(DisplayableException):
    def __init__(self, body: Any, content_type: ContentType):
        super().__init__(f"body {body!r} cannot be serialized as {content_type.value!r}")
