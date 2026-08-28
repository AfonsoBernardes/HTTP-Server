from typing import Any, List, Optional

from displayable_exceptions.http_exception import HTTPServerException
from request.schema import HTTPRequestMethod
from response.schema import HTTPResponseStatusCode
from server.schema import HTTPProtocol


class InvalidHTTPMethod(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    EXPECTED_METHODS = [method.value for method in HTTPRequestMethod]

    def __init__(self, method: str):
        method = method if method else None
        super().__init__(f"invalid HTTP method: expected [{", ".join(self.EXPECTED_METHODS)}], got {method!r}")


class InvalidHTTPProtocol(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    EXPECTED_PROTOCOLS = [protocol.value for protocol in HTTPProtocol]

    def __init__(self, protocol: str):
        protocol = protocol if protocol else None
        super().__init__(f"invalid HTTP protocol: expected [{", ".join(self.EXPECTED_PROTOCOLS)}], got {protocol!r}")


class InvalidHTTPHeaders(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self):
        super().__init__(
            "invalid HTTP headers: make sure headers are key-value pairs, separated by a colon and a line breaker"
        )


class InvalidHTTPHeaderKey(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, key: str, invalid_char: str):
        invalid_char = invalid_char if invalid_char.isprintable() else f"\\x{ord(invalid_char):02x}"
        super().__init__(f"invalid HTTP header key {key!r}: character '{invalid_char}' is not accepted")


class DuplicateHTTPHeader(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, header_key: str, num_values: int):
        super().__init__(f"duplicate HTTP header: expected one value for {header_key!r}, got {num_values!r}")


class UnsupportedTransferEncoding(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_501

    def __init__(self, transfer_encoding: str | List[str]):
        transfer_encoding_string = (
            ",".join(transfer_encoding) if isinstance(transfer_encoding, list) else transfer_encoding
        )

        super().__init__(f"'Transfer-Encoding': {transfer_encoding_string!r} is not supported, only 'chunked'")


class InvalidTransferEncoding(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, transfer_encoding: Optional[Any]):
        transfer_encoding_string = f": {transfer_encoding!r}" if transfer_encoding else ""
        super().__init__(f"'Transfer-Encoding'{transfer_encoding_string} is not valid")


class InvalidChunkSize(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, chunk_size: Optional[Any]):
        chunk_size_string = f"{chunk_size!r}" if chunk_size else ""
        super().__init__(f"chunk size must be a positive integer, got {chunk_size_string}")


class InvalidContentLength(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self, content_length: Optional[Any]):
        content_length_string = f": {content_length!r}" if content_length else ""
        super().__init__(f"'Content-Length'{content_length_string} is not an integer greater or equal to zero")


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
