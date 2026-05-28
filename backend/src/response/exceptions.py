from displayable_exceptions.displayable_exception import DisplayableException


class InvalidHTTPStatusCode(DisplayableException):
    def __init__(self, status_code: int):
        super().__init__(f"invalid HTTP status code {status_code!r}")


class InvalidResponseHeader(DisplayableException):
    def __init__(self):
        super().__init__(f"invalid response header")
