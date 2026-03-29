from displayable_exceptions.displayable_exception import DisplayableException
from response.schema import HTTPResponseStatusCode


class InvalidHTTPStatusCode(DisplayableException):
    def __init__(self, status_code: int):
        super().__init__(f"invalid HTTP status code {status_code!r}")
