from typing import Any, Optional

from displayable_exceptions.http_exception import HTTPServerException
from request.schema import HTTPRequestMethod
from response.schema import HTTPResponseStatusCode


class InvalidDecoding(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self):
        super().__init__("unable to decode request")


class InvalidRequest(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self):
        super().__init__("invalid request; make sure the request follows HTTP/1.X standards")


class UnsupportedTransferEncoding(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_501

    def __init__(self, transfer_encoding: str):
        super().__init__(f"'Transfer-Encoding': {transfer_encoding!r} is not supported, only 'chunked'")


class InvalidTransferEncoding(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, transfer_encoding: Optional[Any]):
        transfer_encoding_string = f": {transfer_encoding!r}" if transfer_encoding else ""
        super().__init__(f"'Transfer-Encoding'{transfer_encoding_string} is not valid ")


class InvalidContentLength(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, content_length: Optional[Any]):
        content_length_string = f": {content_length!r}" if content_length else ""
        super().__init__(f"'Content-Length'{content_length_string} is not a valid positive integer")


class InvalidBodyLength(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, body_length: int, expected_length: int):
        super().__init__(f"expected body with length {expected_length}, got {body_length} bytes")


class BodyTooLarge(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_413

    def __init__(self, max_body_size: int, content_length: int):
        super().__init__(f"expected a body size smaller than {max_body_size!r} bytes, got {content_length!r} bytes")


class UnspecifiedBodyLength(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_411

    def __init__(self, method: HTTPRequestMethod):
        super().__init__(f"expected either 'Transfer-Encoding' or 'Content-Length' for method {method.value!r}")
