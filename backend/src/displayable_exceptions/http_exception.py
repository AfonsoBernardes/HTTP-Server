from uuid import uuid4

from response.schema import HTTPResponseStatusCode


class DisplayableException(Exception):
    def __init__(self, message: str):
        self.base_message = message
        self.exception_id = uuid4()
        self.message = f"{message}: {self.exception_id}"
        super().__init__(self.message)


class HTTPServerException(DisplayableException):
    status_code: HTTPResponseStatusCode

    def __init__(self, message: str = ""):
        super().__init__(message)
