from displayable_exceptions.displayable_exception import DisplayableException
from requests.schema import RequestMethod, RequestProtocol


class InvalidDecoding(DisplayableException):
    def __init__(self):
        super().__init__("unable to decode request")


class InvalidHTTPMethod(DisplayableException):
    EXPECTED_METHODS = [method.value for method in RequestMethod]

    def __init__(self, method: str):
        super().__init__(f"invalid HTTP method: expected [{", ".join(self.EXPECTED_METHODS)}], got {method!r}")


class InvalidHTTPProtocol(DisplayableException):
    EXPECTED_PROTOCOLS = [protocol.value for protocol in RequestProtocol]

    def __init__(self, protocol: str):
        super().__init__(f"invalid HTTP protocol: expected [{", ".join(self.EXPECTED_PROTOCOLS)}], got {protocol!r}")
